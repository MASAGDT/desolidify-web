// frontend/src/components/Preview3D.jsx
import React, { useEffect, useRef, useState } from "react";

/**
 * Simple Three.js STL viewer.
 * Props:
 *  - beforeUrl: object URL for source STL (optional)
 *  - afterUrl: object URL for processed STL (optional)
 */
export default function Preview3D({ beforeUrl = null, afterUrl = null }) {
  const mountRef = useRef(null);
  const stateRef = useRef({
    renderer: null,
    scene: null,
    camera: null,
    mesh: null,
    anim: 0,
    width: 0,
    height: 0,
    three: null,
    STLLoader: null,
    root: null,
  });
  const [ready, setReady] = useState(false);

  // Lazy-load vendor modules once
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const three = await import("/vendor/three/three.module.js");
        const STL = await import("/vendor/three/STLLoader.js");
        if (!mounted) return;
        stateRef.current.three = three;
        stateRef.current.STLLoader = STL.STLLoader || STL.default?.STLLoader || STL.default || STL;
        setReady(true);
      } catch (e) {
        // module load failed; leave viewer blank
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  // Initialize renderer + scene
  useEffect(() => {
    if (!ready || !mountRef.current) return;
    const S = stateRef.current;
    if (S.renderer) return;

    const THREE = S.three;
    const el = mountRef.current;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
    renderer.setClearColor(0x000000, 0);
    el.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, 1, 0.01, 10000);
    camera.position.set(100, 120, 160);

    const root = new THREE.Group();
    scene.add(root);

    const amb = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(amb);
    const dir = new THREE.DirectionalLight(0xffffff, 0.8);
    dir.position.set(1, 1.2, 0.7).multiplyScalar(200);
    scene.add(dir);

    S.renderer = renderer;
    S.scene = scene;
    S.camera = camera;
    S.root = root;

    const resize = () => {
      const rect = el.getBoundingClientRect();
      const w = Math.max(10, rect.width | 0);
      const h = Math.max(10, rect.height | 0);
      if (w === S.width && h === S.height) return;
      S.width = w;
      S.height = h;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    };
    resize();
    S._onResize = resize;
    window.addEventListener("resize", resize);

    const animate = () => {
      S.anim = requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };
    animate();

    // rudimentary mouse rotate
    let dragging = false;
    let lx = 0, ly = 0;
    const onDown = (e) => { dragging = true; lx = e.clientX; ly = e.clientY; };
    const onUp = () => { dragging = false; };
    const onMove = (e) => {
      if (!dragging || !S.root) return;
      const dx = (e.clientX - lx) * 0.005;
      const dy = (e.clientY - ly) * 0.005;
      S.root.rotation.y += dx;
      S.root.rotation.x += dy;
      lx = e.clientX; ly = e.clientY;
    };
    el.addEventListener("mousedown", onDown);
    window.addEventListener("mouseup", onUp);
    window.addEventListener("mousemove", onMove);

    return () => {
      window.removeEventListener("resize", resize);
      el.removeEventListener("mousedown", onDown);
      window.removeEventListener("mouseup", onUp);
      window.removeEventListener("mousemove", onMove);
      if (S.anim) cancelAnimationFrame(S.anim);
      if (S.renderer) {
        try { S.renderer.dispose(); } catch {}
        try { el.removeChild(S.renderer.domElement); } catch {}
      }
      S.renderer = null;
      S.scene = null;
      S.camera = null;
      S.root = null;
    };
  }, [ready]);

  // Load current STL (prefers afterUrl if present)
  useEffect(() => {
    const url = afterUrl || beforeUrl;
    const S = stateRef.current;
    if (!ready || !url || !S.three || !S.STLLoader || !S.root) {
      // clear if no url
      if (S.mesh && S.root) {
        S.root.remove(S.mesh);
        S.mesh.geometry?.dispose?.();
        S.mesh.material?.dispose?.();
        S.mesh = null;
      }
      return;
    }
    let canceled = false;
    const THREE = S.three;
    const loader = new S.STLLoader();

    loader.load(
      url,
      (geom) => {
        if (canceled) return;
        if (S.mesh && S.root) {
          S.root.remove(S.mesh);
          S.mesh.geometry?.dispose?.();
          S.mesh.material?.dispose?.();
          S.mesh = null;
        }
        // Ensure BufferGeometry
        const geometry = geom.isBufferGeometry ? geom : new THREE.BufferGeometry().fromGeometry(geom);
        geometry.computeVertexNormals();

        const mat = new THREE.MeshStandardMaterial({
          color: afterUrl ? 0x6aa7ff : 0xaaaaaa,
          roughness: 0.6,
          metalness: 0.05,
        });
        const mesh = new THREE.Mesh(geometry, mat);
        S.root.add(mesh);
        S.mesh = mesh;

        // Frame camera to mesh
        geometry.computeBoundingBox();
        const bb = geometry.boundingBox;
        const size = new THREE.Vector3();
        bb.getSize(size);
        const center = new THREE.Vector3();
        bb.getCenter(center);
        mesh.position.sub(center);

        const maxDim = Math.max(size.x, size.y, size.z) || 1;
        const dist = maxDim * 2.2;
        S.camera.position.set(dist, dist * 0.9, dist * 1.2);
        S.camera.near = Math.max(0.01, dist / 100);
        S.camera.far = dist * 10;
        S.camera.lookAt(0, 0, 0);
        S.camera.updateProjectionMatrix();
      },
      undefined,
      () => {
        // ignore errors (keep previous mesh if any)
      }
    );

    return () => {
      canceled = true;
    };
  }, [beforeUrl, afterUrl, ready]);

  return (
    <div
      ref={mountRef}
      style={{
        width: "100%",
        height: 300,
        background:
          "linear-gradient(180deg, rgba(17,18,24,0.8), rgba(12,14,20,0.8))",
      }}
    >
      {!ready && (
        <div style={{ padding: 12, color: "var(--muted)", fontSize: 12 }}>
          Viewer initializing…
        </div>
      )}
    </div>
  );
}
