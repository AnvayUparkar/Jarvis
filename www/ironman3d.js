// This script loads and animates a 3D Iron Man helmet model using Three.js.
// It requires GLTFLoader.js to be loaded before this script.

(function() {
  // Get the container element for the 3D model
  const container = document.getElementById("ironman-3d-container");
  
  // If the container doesn't exist, log an error and exit
  if (!container) {
    console.error("3D container 'ironman-3d-container' not found in the DOM.");
    return;
  }

  // Create a new Three.js scene
  const scene = new THREE.Scene();
  // Set the background color of the scene to black
  scene.background = new THREE.Color(0x000000);

  // Create a perspective camera
  // Parameters: FOV, Aspect Ratio, Near Clipping Plane, Far Clipping Plane
  const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
  // Set the camera's position (x, y, z)
  camera.position.set(0, 1, 3);

  // Create a WebGL renderer with antialiasing and alpha (transparent background)
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  // Set the size of the renderer to match the container
  renderer.setSize(container.clientWidth, container.clientHeight);
  // Append the renderer's DOM element (canvas) to the container
  container.appendChild(renderer.domElement);

  // Add a point light to the scene
  // Parameters: Color, Intensity, Distance
  const light = new THREE.PointLight(0x00ffff, 2, 100); // Cyan light
  light.position.set(0, 5, 5); // Position the light
  scene.add(light); // Add light to the scene

  // Add an ambient light to the scene (soft light that illuminates all objects equally)
  // Parameters: Color, Intensity
  const ambient = new THREE.AmbientLight(0x00ffff, 0.5); // Soft cyan ambient light
  scene.add(ambient); // Add ambient light to the scene

  // Create a GLTFLoader instance for loading GLTF models
  const loader = new THREE.GLTFLoader();
  // Load the Iron Man helmet GLB model
  loader.load("/www/assets/models/ironman_helmet.glb", gltf => {
    // Get the loaded model (scene property of the GLTF object)
    const model = gltf.scene;
    // Scale the model
    model.scale.set(1.5, 1.5, 1.5);
    // Position the model
    model.position.set(0, -1.5, 0);
    // Add the model to the scene
    scene.add(model);

    // Animation loop function
    function animate() {
      // Request the next animation frame (standard for Three.js animations)
      requestAnimationFrame(animate);
      // Rotate the model around the Y-axis
      model.rotation.y += 0.01;
      // Render the scene with the camera
      renderer.render(scene, camera);
    }

    // Start the animation loop
    animate();
  }, undefined, error => {
    // Error callback for GLTF loading
    console.error("An error occurred while loading the GLTF model:", error);
  });

  // Handle window resizing to make the 3D scene responsive
  window.addEventListener('resize', () => {
    // Update camera aspect ratio
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    // Update renderer size
    renderer.setSize(container.clientWidth, container.clientHeight);
  });
})();
