import cv2, time, numpy as np, mediapipe as mp
from collections import deque

# ---- tune these ----
EAR_T = 0.21  # below = eyes closed
YAW_T = 0.18  # head turn ratio
GAZE_T = 0.17  # iris offset from center (0.5)
DROWSY_SEC = 1.5  # continuous eye closure
AWAY_SEC = 2.0  # continuous looking away
PERCLOS_T = 0.4  # % of last 30s eyes closed
PITCH_NEUTRAL = 0.46  # nose-to-chin ratio when looking straight

L_EYE = [362, 385, 387, 263, 373, 380]
R_EYE = [33, 160, 158, 133, 153, 144]

NO_FACE = {"yaw": 0, "pitch": 0, "roll": 0, "gaze": "No face", "face": False}


class Analyzer:
    def __init__(self):
        self.mesh = mp.solutions.face_mesh.FaceMesh(
            refine_landmarks=True, max_num_faces=1
        )
        self.reset()

    def reset(self):
        self.state = "Focused"
        self.t_state = {"Focused": 0.0, "Distracted": 0.0, "Drowsy": 0.0}
        self.closed_since = self.away_since = None
        self.hist = deque()
        self.blinks, self._was_closed = 0, False
        self.streak = self.best_streak = 0.0
        self.last, self._last_log = time.time(), 0
        self.log = []  # rows for CSV
        self.pose = dict(NO_FACE)

    @staticmethod
    def _ear(pt, ids):
        p = [pt(i) for i in ids]
        return (np.linalg.norm(p[1] - p[5]) + np.linalg.norm(p[2] - p[4])) / (
            2 * np.linalg.norm(p[0] - p[3])
        )

    @staticmethod
    def _gaze(pt):
        r = (pt(468)[0] - pt(33)[0]) / (pt(133)[0] - pt(33)[0] + 1e-6)
        l = (pt(473)[0] - pt(362)[0]) / (pt(263)[0] - pt(362)[0] + 1e-6)
        return (r + l) / 2  # ~0.5 = looking at screen

    def process(self, frame):
        now = time.time()
        dt = now - self.last
        self.last = now
        h, w = frame.shape[:2]
        res = self.mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        closed, away, ear = False, True, 0.0

        if res.multi_face_landmarks:
            lm = res.multi_face_landmarks[0].landmark
            pt = lambda i: np.array([lm[i].x * w, lm[i].y * h])
            ear = (self._ear(pt, L_EYE) + self._ear(pt, R_EYE)) / 2
            closed = ear < EAR_T
            face_w = np.linalg.norm(pt(454) - pt(234))
            yaw = (pt(1)[0] - (pt(234)[0] + pt(454)[0]) / 2) / face_w
            g = self._gaze(pt)
            gaze_off = abs(g - 0.5)
            away = abs(yaw) > YAW_T or (not closed and gaze_off > GAZE_T)

            eye_y = (pt(33)[1] + pt(263)[1]) / 2
            ratio = (pt(1)[1] - eye_y) / (pt(152)[1] - eye_y + 1e-6)
            roll = np.degrees(
                np.arctan2(pt(263)[1] - pt(33)[1], pt(263)[0] - pt(33)[0])
            )
            gaze = (
                "Left"
                if g < 0.5 - GAZE_T
                else "Right"
                if g > 0.5 + GAZE_T
                else "Center"
            )
            self.pose = {
                "yaw": round(yaw * 90),
                "pitch": round((ratio - PITCH_NEUTRAL) * 150),
                "roll": round(roll),
                "gaze": gaze,
                "face": True,
            }
        else:
            self.pose = dict(NO_FACE)

        # blinks
        if self._was_closed and not closed:
            self.blinks += 1
        self._was_closed = closed

        # timers
        self.closed_since = (self.closed_since or now) if closed else None
        self.away_since = (self.away_since or now) if away else None
        self.hist.append((now, closed))
        while self.hist and now - self.hist[0][0] > 30:
            self.hist.popleft()
        perclos = sum(c for _, c in self.hist) / max(len(self.hist), 1)

        # state
        if (
            self.closed_since and now - self.closed_since > DROWSY_SEC
        ) or perclos > PERCLOS_T:
            self.state = "Drowsy"
        elif self.away_since and now - self.away_since > AWAY_SEC:
            self.state = "Distracted"
        else:
            self.state = "Focused"

        # stats
        self.t_state[self.state] += dt
        if self.state == "Focused":
            self.streak += dt
            self.best_streak = max(self.best_streak, self.streak)
        else:
            self.streak = 0
        if now - self._last_log >= 1:
            self._last_log = now
            self.log.append(
                [time.strftime("%H:%M:%S"), self.state, round(ear, 3), self.blinks]
            )

        # overlay
        color = {
            "Focused": (0, 200, 0),
            "Distracted": (0, 200, 255),
            "Drowsy": (0, 0, 255),
        }[self.state]
        cv2.putText(
            frame,
            f"{self.state}  EAR:{ear:.2f}",
            (15, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            color,
            2,
        )
        return frame

    def stats(self):
        total = max(sum(self.t_state.values()), 1e-6)
        pct = lambda k: round(100 * self.t_state[k] / total)
        return {
            "state": self.state,
            "score": pct("Focused"),
            "focused_pct": pct("Focused"),
            "distracted_pct": pct("Distracted"),
            "drowsy_pct": pct("Drowsy"),
            "streak_s": round(self.streak),
            "best_streak_min": round(self.best_streak / 60, 1),
            "blinks": self.blinks,
            "duration_s": round(total),
            **self.pose,
        }
