var Scene = {};
(function(t, s) {

    var mouse3D;
    var theta = 45;

    init();
    animate();

    function init() {
        s.container = $("<div id='screen0'></div>")
        $("body").append(s.container);

        s.camera = new t.Camera(40, window.innerWidth / window.innerHeight, 1, 10000 );
        s.camera.position.y  = 800;
        s.camera.target.position.y = 200;

        s.scene = new t.Scene();
        var scene = s.scene;

        // roll-over helpers
        s.rollOverGeo = new t.Cube(50, 50, 50);
        s.rollOverMaterial = new t.MeshBasicMaterial({color: 0xff0000, opacity: 0.5, transparent: true});
        s.rollOverMesh = new t.Mesh(s.rollOverGeo, s.rollOverMaterial);
        scene.addObject(s.rollOverMesh);

        // cubes
        s.cubeGeo = new t.Cube(50, 50, 50);
        s.cubeMaterial = new t.MeshBasicMaterial({color: 0x00ff80, shading: t.FlatShading });

        // picking
        s.projector = new t.Projector();
        // grid
        s.plane = new t.Mesh(new t.Plane(1000,1000,32,32),
                           new t.MeshBasicMaterial({color: 0x555555, wireframe: true}));
        s.plane.rotation.x = -90 * Math.PI / 180;
        scene.addObject(s.plane);

        s.mouse2D = new t.Vector3(0, 10000, 0.5);
        s.ray = new t.Ray(s.camera.position, null);

        // Lights
        var ambientLight = new t.AmbientLight(0x606060);
        scene.addLight(ambientLight);

        var directionalLight = new t.DirectionalLight(0xffffff);
        directionalLight.position.x = Math.random() - 0.5;
        directionalLight.position.y = Math.random() - 0.5;
        directionalLight.position.z = Math.random() - 0.5;
        directionalLight.position.normalize();
        scene.addLight(directionalLight);

        var directionalLight = new t.DirectionalLight(0x808080);
        directionalLight.position.x = Math.random() - 0.5;
        directionalLight.position.y = Math.random() - 0.5;
        directionalLight.position.z = Math.random() - 0.5;
        directionalLight.position.normalize();
        scene.addLight(directionalLight);

        // scene rendering
        s.renderer = new t.WebGLRenderer( { antialias: true } );
        s.renderer.setSize(window.innerWidth, window.innerHeight);

        s.container.append(s.renderer.domElement);

        s.stats = new Stats();
        s.stats.domElement.style.position = 'absolute';
        s.stats.domElement.style.left = '0px';
        s.stats.domElement.style.top = '0px';
        $("body").append(s.stats.domElement);

        console.log("initialized");
    }

    function animate() { 
        requestAnimationFrame(animate);
        render();
        s.stats.update();
    }

    function render() {
        mouse3D = s.projector.unprojectVector( s.mouse2D.clone(), s.camera );
        s.ray.direction = mouse3D.subSelf( s.camera.position ).normalize();
        var intersects = s.ray.intersectScene(s.scene);
        if ( intersects.length > 0 ) {
            console.log("intersected : " + intersects.length);
        }
        s.camera.position.x = 1400 * Math.sin(theta * Math.PI / 360)
        s.camera.position.y = 1400 * Math.cos(theta * Math.PI / 360)
        s.renderer.render(s.scene, s.camera);
        console.log("=>");
    }

}(THREE, Scene));


