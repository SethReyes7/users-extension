(function() {
  const randomDate = (start, end) => {
    const date = new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime()));
    return date.toISOString().split("T")[0];
  };

  const generarTelefono = () => {
    return "33" + Math.floor(10000000 + Math.random() * 90000000).toString();
  };

  window.llenarPaso1 = () => {
    document.querySelector('input[name="nombre"]').value = "Juan";
    document.querySelector('input[name="apellidoPaterno"]').value = "Testuser";
    document.querySelector('input[name="apellidoMaterno"]').value = "Prueba";

    const sexoRadio = document.querySelector('input[type="radio"][name="sexo"][value="M"]');
    if (sexoRadio) sexoRadio.checked = true;

    const hoy = new Date();
    const edadMinima = new Date(hoy.getFullYear() - 18, hoy.getMonth(), hoy.getDate());
    document.querySelector('input[name="fechaNacimiento"]').value = randomDate(new Date(1970, 0, 1), edadMinima);

    document.querySelector('select[name="estadoNacimiento"]').value = "Jalisco";
    document.querySelector('input[name="telefono"]').value = generarTelefono();
  };

  window.llenarPaso2 = () => {
    document.querySelector('input[name="calle"]').value = "Calle Falsa 123";
    document.querySelector('input[name="colonia"]').value = "Centro";
    document.querySelector('input[name="cp"]').value = "44100";
    document.querySelector('select[name="estado"]').value = "Jalisco";
    document.querySelector('select[name="municipio"]').value = "Guadalajara";
  };

  window.llenarPaso3 = () => {
    document.querySelector('input[name="ingresoIndividual"]').value = "10000";
    document.querySelector('input[name="ingresoFamiliar"]').value = "15000";
    document.querySelector('select[name="historialCrediticio"]').value = "Bueno";
  };
})();
