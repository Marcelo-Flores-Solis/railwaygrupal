class Cuenta {
    constructor(email, password, rememberMe) {
        this.email = email;
        this.password = password;
        this.rememberMe = rememberMe;
        this.fechaCreacion = new Date();
    }

    mostrarInfo() {
        console.log("--- Información de la Cuenta ---");
        console.log(`Correo: ${this.email}`);
        console.log(`Contraseña: ${this.password.replace(/./g, '*')}`);
        console.log(`Recuérdame: ${this.rememberMe ? 'Sí' : 'No'}`);
        console.log(`Fecha de intento de inicio de sesión: ${this.fechaCreacion.toLocaleString()}`);
        console.log("-------------------------------");
    }
}

const form = document.querySelector('form');

form.addEventListener('submit', function(event) {
    event.preventDefault();

    const emailInput = document.getElementById('email').value;
    const passwordInput = document.getElementById('password').value;
    const rememberMeChecked = document.getElementById('remember').checked;

    const nuevaCuenta = new Cuenta(emailInput, passwordInput, rememberMeChecked);

    console.log("¡Datos capturados!");
    nuevaCuenta.mostrarInfo();
});
