document.addEventListener('DOMContentLoaded', () => {

    // ======================================================
    // 1. GESTIÓN DE SESIÓN (Logueado o no)
    // ======================================================
    const usuarioGuardado = localStorage.getItem('usuario_zebra');
    let usuario = null;

    if (usuarioGuardado) {
        usuario = JSON.parse(usuarioGuardado);
        console.log("Usuario activo:", usuario.nombre);
        
        // Actualizar el menú de navegación si existe
        const linkLogin = document.querySelector('a[href="/login"]');
        if (linkLogin) {
            linkLogin.innerText = `Hola, ${usuario.nombre}`;
            linkLogin.href = "/usuario";
        }
    }

    // ======================================================
    // 2. PÁGINA DE PERFIL (user.html)
    // ======================================================
    const perfilNombre = document.getElementById('perfil-nombre');
    
    // Si estamos en la página de perfil (porque existe el elemento 'perfil-nombre')
    if (perfilNombre) {
        if (!usuario) {
            // Si no hay usuario logueado, patada al login
            window.location.href = '/login';
        } else {
            // Rellenar datos
            document.getElementById('perfil-nombre').innerText = usuario.nombre;
            document.getElementById('perfil-email').innerText = usuario.email;
        }

        // Configurar botones de Cerrar Sesión
        const botonesLogout = [document.getElementById('btn-logout-nav'), document.getElementById('btn-logout-main')];
        
        botonesLogout.forEach(btn => {
            if (btn) {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    if(confirm("¿Seguro que quieres cerrar sesión?")) {
                        localStorage.removeItem('usuario_zebra'); // Borrar sesión
                        window.location.href = '/login'; // Ir al login
                    }
                });
            }
        });
    }

    // ======================================================
    // 3. REGISTRO (register.html)
    // ======================================================
    const formRegistro = document.getElementById('form-registro');

    if (formRegistro) {
        formRegistro.addEventListener('submit', (e) => {
            e.preventDefault(); // Evita recarga normal

            const nombre = document.getElementById('nombre').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            console.log("Enviando registro...", { nombre, email });

            fetch('/api/registro', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nombre, email, password })
            })
            .then(res => {
                if (res.ok) return res.json();
                throw new Error('Error al registrar. El email podría estar duplicado.');
            })
            .then(data => {
                alert('¡Cuenta creada con éxito! Ahora inicia sesión.');
                window.location.href = '/login';
            })
            .catch(err => {
                console.error(err);
                alert(err.message);
            });
        });
    }

    // ======================================================
    // 4. LOGIN (login.html)
    // ======================================================
    // Asegúrate de ponerle id="form-login" a tu <form> en login.html
    const formLogin = document.getElementById('form-login');

    if (formLogin) {
        formLogin.addEventListener('submit', (e) => {
            e.preventDefault();

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            })
            .then(res => {
                if (res.ok) return res.json();
                throw new Error('Usuario o contraseña incorrectos');
            })
            .then(dataUsuario => {
                // GUARDAR SESIÓN EN EL NAVEGADOR
                localStorage.setItem('usuario_zebra', JSON.stringify(dataUsuario));
                alert(`¡Bienvenido, ${dataUsuario.nombre}!`);
                window.location.href = '/catalogo';
            })
            .catch(err => alert(err.message));
        });
    }

    // ======================================================
    // 5. CATÁLOGO Y BUSCADOR (catalogo.html)
    // ======================================================
    const contenedorLibros = document.getElementById('contenedor-libros');
    const inputBuscador = document.getElementById('buscador');
    let librosMemoria = []; 

    const mostrarLibros = (libros) => {
        contenedorLibros.innerHTML = ""; 
        if (libros.length === 0) {
            contenedorLibros.innerHTML = "<h3 style='text-align:center; width:100%; color:#666;'>Sin resultados.</h3>";
            return;
        }
        libros.forEach(libro => {
            const tarjeta = document.createElement('div');
            tarjeta.className = 'tarjeta-libro';
            tarjeta.innerHTML = `
                <a href="/detalle?id=${libro.id}" style="text-decoration: none; color: inherit;">
                    <img src="${libro.img}" alt="${libro.titulo}" onerror="this.src='https://via.placeholder.com/150'">
                    <h4>${libro.titulo}</h4>
                    <p>${libro.autor}</p>
                    <span class="etiqueta ${libro.disponible ? 'disponible' : 'agotado'}">
                        ${libro.disponible ? 'Disponible' : 'No Disponible'}
                    </span>
                </a>
            `;
            contenedorLibros.appendChild(tarjeta);
        });
    };

    if (contenedorLibros) { 
        fetch('/api/libros')
            .then(r => r.json())
            .then(data => { librosMemoria = data; mostrarLibros(data); });

        if (inputBuscador) {
            inputBuscador.addEventListener('input', (e) => {
                const txt = e.target.value.toLowerCase();
                mostrarLibros(librosMemoria.filter(l => l.titulo.toLowerCase().includes(txt) || l.autor.toLowerCase().includes(txt)));
            });
        }
    }

    // ======================================================
    // 6. DETALLE Y PRÉSTAMO (element.html)
    // ======================================================
    const tituloDetalle = document.getElementById('detalle-titulo');

    if (tituloDetalle) {
        const params = new URLSearchParams(window.location.search);
        const idLibro = params.get('id');

        // Cargar info del libro
        if (idLibro) {
            fetch(`/api/libro?id=${idLibro}`)
                .then(r => r.json())
                .then(libro => {
                    document.getElementById('detalle-titulo').innerText = libro.titulo;
                    document.getElementById('detalle-autor').innerText = libro.autor;
                    document.getElementById('detalle-sinopsis').innerText = libro.sinopsis;
                    document.getElementById('detalle-img').src = libro.img;
                    
                    // Lógica del botón prestar
                    const btnPrestar = document.getElementById('btn-prestar'); // Necesitas ponerle este ID al botón en element.html
                    if(btnPrestar) {
                        if(libro.disponible == 0) {
                            btnPrestar.innerText = "No Disponible";
                            btnPrestar.style.backgroundColor = "#ccc";
                            btnPrestar.disabled = true;
                        } else {
                            btnPrestar.addEventListener('click', () => {
                                if(!usuario) {
                                    alert("Inicia sesión para pedir libros.");
                                    window.location.href = '/login';
                                    return;
                                }
                                if(confirm("¿Confirmar préstamo?")) {
                                    fetch('/api/prestar', {
                                        method: 'POST',
                                        headers: {'Content-Type': 'application/json'},
                                        body: JSON.stringify({ id_libro: idLibro })
                                    }).then(() => {
                                        alert("¡Libro Prestado!");
                                        location.reload();
                                    });
                                }
                            });
                        }
                    }
                });
        }
    }
});