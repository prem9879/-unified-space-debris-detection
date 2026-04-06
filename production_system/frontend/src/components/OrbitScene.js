import { jsx as _jsx } from "react/jsx-runtime";
import { useEffect, useRef } from "react";
import * as THREE from "three";
export function OrbitScene() {
    const mountRef = useRef(null);
    useEffect(() => {
        if (!mountRef.current)
            return;
        const width = mountRef.current.clientWidth;
        const height = 360;
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
        camera.position.set(0, 0, 8);
        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(width, height);
        mountRef.current.appendChild(renderer.domElement);
        const light = new THREE.PointLight(0xffffff, 2.2);
        light.position.set(6, 3, 8);
        scene.add(light);
        const earth = new THREE.Mesh(new THREE.SphereGeometry(1.4, 40, 40), new THREE.MeshStandardMaterial({ color: 0x2f7cff, roughness: 0.7, metalness: 0.1 }));
        scene.add(earth);
        const orbitRing = new THREE.Mesh(new THREE.TorusGeometry(2.6, 0.018, 8, 180), new THREE.MeshBasicMaterial({ color: 0x39d2ff }));
        orbitRing.rotation.x = Math.PI / 2.8;
        scene.add(orbitRing);
        const debris = new THREE.Mesh(new THREE.SphereGeometry(0.08, 16, 16), new THREE.MeshStandardMaterial({ color: 0xff6d4d }));
        scene.add(debris);
        let t = 0;
        const animate = () => {
            t += 0.012;
            earth.rotation.y += 0.006;
            debris.position.set(Math.cos(t) * 2.6, Math.sin(t * 1.2) * 0.4, Math.sin(t) * 2.6);
            renderer.render(scene, camera);
            requestAnimationFrame(animate);
        };
        animate();
        return () => {
            renderer.dispose();
            mountRef.current?.removeChild(renderer.domElement);
        };
    }, []);
    return _jsx("div", { className: "panel overflow-hidden", ref: mountRef });
}
