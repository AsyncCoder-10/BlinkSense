(function () {
  const box = document.getElementById("stage3d");
  const W = box.clientWidth, H = box.clientHeight;

  const scene = new THREE.Scene();
  const cam = new THREE.PerspectiveCamera(35, W / H, 0.1, 100);
  cam.position.set(0, 0.3, 7);
  cam.lookAt(0, -0.1, 0);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(W, H);
  box.appendChild(renderer.domElement);

  scene.add(new THREE.AmbientLight(0xffffff, 0.75));
  const sun = new THREE.DirectionalLight(0xffffff, 0.9);
  sun.position.set(3, 4, 5);
  scene.add(sun);

  const skin = new THREE.MeshStandardMaterial({ color: 0x60a5fa, roughness: 0.45, metalness: 0.1 });
  const dark = new THREE.MeshStandardMaterial({ color: 0x1e3a8a });
  const white = new THREE.MeshStandardMaterial({ color: 0xffffff });

  // static neck + shoulders + floor ring
  const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.38, 0.8, 24), skin);
  neck.position.y = -1.35;
  scene.add(neck);
const shoulders = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 16), dark);  shoulders.scale.set(1.9, 0.45, 0.9);
  shoulders.position.y = -2.0;
  scene.add(shoulders);
  const ring = new THREE.Mesh(new THREE.RingGeometry(1.7, 1.78, 64),
    new THREE.MeshBasicMaterial({ color: 0x2563eb, side: THREE.DoubleSide, transparent: true, opacity: 0.35 }));
  ring.rotation.x = Math.PI / 2;
  ring.position.y = -2.4;
  scene.add(ring);

  // head (this group rotates)
  const head = new THREE.Group();
  head.rotation.order = "YXZ";

  const skull = new THREE.Mesh(new THREE.SphereGeometry(1, 48, 48), skin);
  skull.scale.set(0.85, 1.05, 0.95);
  head.add(skull);

  const wire = new THREE.Mesh(new THREE.SphereGeometry(1.03, 18, 14),
    new THREE.MeshBasicMaterial({ color: 0xffffff, wireframe: true, transparent: true, opacity: 0.2 }));
  wire.scale.copy(skull.scale);
  head.add(wire);

  [-0.32, 0.32].forEach(x => {
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.14, 24, 24), white);
    eye.position.set(x, 0.15, 0.84);
    head.add(eye);
    const pupil = new THREE.Mesh(new THREE.SphereGeometry(0.07, 16, 16), dark);
    pupil.position.set(x, 0.15, 0.96);
    head.add(pupil);
  });

  const nose = new THREE.Mesh(new THREE.ConeGeometry(0.12, 0.35, 24), dark);
  nose.rotation.x = Math.PI / 2;
  nose.position.set(0, -0.1, 0.98);
  head.add(nose);

  [-0.85, 0.85].forEach(x => {
    const ear = new THREE.Mesh(new THREE.SphereGeometry(0.16, 16, 16), skin);
    ear.scale.set(0.5, 1, 0.8);
    ear.position.set(x, 0, 0);
    head.add(ear);
  });

  // forward arrow shows where the head points
  head.add(new THREE.ArrowHelper(new THREE.Vector3(0, 0, 1), new THREE.Vector3(0, -0.1, 1.2), 0.9, 0xf59e0b, 0.25, 0.15));

  head.position.y = 0.1;
  scene.add(head);

  const target = { x: 0, y: 0, z: 0 };
  const rad = Math.PI / 180;
  const clamp = (v, m) => Math.max(-m, Math.min(m, v));

  window.setHead = function (yaw, pitch, roll, face) {
    target.y = clamp(yaw, 75) * rad;
    target.x = clamp(pitch, 55) * rad;
    target.z = -clamp(roll, 60) * rad;
    skin.color.set(face ? 0x60a5fa : 0x94a3b8);
  };

  (function loop() {
    requestAnimationFrame(loop);
    head.rotation.x += (target.x - head.rotation.x) * 0.15;
    head.rotation.y += (target.y - head.rotation.y) * 0.15;
    head.rotation.z += (target.z - head.rotation.z) * 0.15;
    renderer.render(scene, cam);
  })();
})();