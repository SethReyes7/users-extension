const randomDate = (start, end) => {
  const date = new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime()));
  return date.toISOString().split("T")[0];
};

const generarTelefono = () => {
  return "33" + Math.floor(10000000 + Math.random() * 90000000).toString();
};

async function ejecutarPaso(func, ...args) {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: func,
    args: args
  });
}


const setInputValue = (selector, value) => {
  const el = document.querySelector(selector);
  if (el) {
    el.value = value;
    el.dispatchEvent(new Event("input", { bubbles: true }));
  }
};

const ejecutarPaso1ConTipo = (tipo) => {
  ejecutarPaso((tipoArg) => {
    const randomDate = (start, end) => {
      const date = new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime()));
      return date.toISOString().split("T")[0];
    };

    const setInputValue = (selector, value) => {
      const el = document.querySelector(selector);
      if (el) {
        el.value = value;
        el.dispatchEvent(new Event("input", { bubbles: true }));
      }
    };

    const clickContinuar = () => {
      const continuarBtn = Array.from(document.querySelectorAll('button')).find(
        btn => btn.textContent.trim().toLowerCase() === "continuar"
      );
      if (continuarBtn) setTimeout(() => continuarBtn.click(), 300);
    };

    const generarTelefono = () => {
      return "33" + Math.floor(10000000 + Math.random() * 90000000).toString();
    };

    // 🧠 Valores según tipo
    let nombre = "Juan";
    let paterno = "Testuser";
    const materno = "Prueba";

    switch (tipoArg) {
      case "veriffRechazado":
        nombre = "rejected";
        break;
      case "veriffManual":
        paterno = "blue prueba";
        break;
      case "facematch":
        paterno = "idv prueba";
        break;
    }

    // 👤 Datos personales
    setInputValue('input[name="personal.name"]', nombre);
    setInputValue('input[name="personal.first_name"]', paterno);
    setInputValue('input[name="personal.last_name"]', materno);

    const sexoRadio = document.querySelector('input[type="radio"][name="personal.gender"][value="H"]');
    if (sexoRadio) sexoRadio.click();

    const hoy = new Date();
    const minFecha = new Date(hoy.getFullYear() - 50, hoy.getMonth(), hoy.getDate());
    const maxFecha = new Date(hoy.getFullYear() - 18, hoy.getMonth(), hoy.getDate());
    const fechaInput = document.querySelector('input[name="personal.birthday"]');
    if (fechaInput) {
      fechaInput.value = randomDate(minFecha, maxFecha);
      fechaInput.dispatchEvent(new Event("input", { bubbles: true }));
    }

    const selects = document.querySelectorAll('select.k-ds-body-02');
    const estadoSel = Array.from(selects).find(sel =>
      Array.from(sel.options).some(opt => opt.value === "Jalisco")
    );

    if (estadoSel) {
      estadoSel.value = "Jalisco";
      estadoSel.dispatchEvent(new Event("input", { bubbles: true }));
      estadoSel.dispatchEvent(new Event("change", { bubbles: true }));
      estadoSel.focus();
      estadoSel.blur();
    }

    setInputValue('input[name="contact.mobile"]', generarTelefono());

    const triggerEventos = (el) => {
      el.focus();
      el.dispatchEvent(new Event("input", { bubbles: true }));
      el.dispatchEvent(new Event("change", { bubbles: true }));
      el.dispatchEvent(new KeyboardEvent("keydown", { key: "a", bubbles: true }));
      el.dispatchEvent(new KeyboardEvent("keyup", { key: "a", bubbles: true }));
      el.dispatchEvent(new Event("blur", { bubbles: true }));
    };

    const nombreEl = document.querySelector('input[name="personal.name"]');
    const paternoEl = document.querySelector('input[name="personal.first_name"]');
    const maternoEl = document.querySelector('input[name="personal.last_name"]');
    const telefonoEl = document.querySelector('input[name="contact.mobile"]');

    [nombreEl, paternoEl, maternoEl, fechaInput, estadoSel].forEach(el => {
      if (el) triggerEventos(el);
    });

    if (telefonoEl) {
      setTimeout(() => {
        telefonoEl.focus();
        if (maternoEl) maternoEl.blur();
      }, 200);
    }

    const waitForValue = (selector, intentos = 20, intervalo = 300) => {
      return new Promise((resolve) => {
        const intentar = () => {
          const el = document.querySelector(selector);
          if (el && el.value && el.value.trim().length > 0) {
            resolve();
          } else if (intentos > 0) {
            setTimeout(() => intentar(--intentos), intervalo);
          } else {
            console.warn("⛔ Timeout esperando CURP");
            resolve(); // de todas formas continuar
          }
        };
        intentar();
      });
    };
    
    waitForValue('input[name="personal.curp"]').then(() => {
      clickContinuar();
    });
  }, tipo);
};


// Asignación de botones por tipo de usuario
document.getElementById("btnPaso1VeriffAprobado")
        .addEventListener("click", () => ejecutarPaso1ConTipo("veriffAprobado"));
document.getElementById("btnPaso1VeriffRechazado")
        .addEventListener("click", () => ejecutarPaso1ConTipo("veriffRechazado"));
document.getElementById("btnPaso1VeriffManual")
        .addEventListener("click", () => ejecutarPaso1ConTipo("veriffManual"));
document.getElementById("btnPaso1Facematch")
        .addEventListener("click", () => ejecutarPaso1ConTipo("facematch"));



document.getElementById("btnRegistro").addEventListener("click", () => {
  ejecutarPaso(() => {
    const setInputValue = (selector, value) => {
      const el = document.querySelector(selector);
      if (el) {
        el.value = value;
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
        el.dispatchEvent(new Event("blur", { bubbles: true }));
      }
    };

    const clickCrearCuenta = () => {
      const continuarBtn = document.getElementById("buttonRegistroId");
      if (continuarBtn) {
        setTimeout(() => continuarBtn.click(), 300);
      } else {
        console.warn("Botón 'Crear cuenta' no encontrado.");
      }
    };

    const timestamp = Date.now().toString().slice(-10);
    const email = `seth.reyes+${timestamp}@kueski.com`;
    const password = "Test1234";

    setInputValue('input[name="email"]', email);
    setInputValue('input[name="password"]', password);

    console.log("📧 Email generado:", email);

    setTimeout(clickCrearCuenta, 800);
  });
        });
        

        document.getElementById("btnPaso2").addEventListener("click", () => {
  ejecutarPaso(() => {
    const setInputValue = (selector, value) => {
      const el = document.querySelector(selector);
      if (el) {
        el.value = value;
        el.dispatchEvent(new Event("input", { bubbles: true }));
      }
    };

    const clickContinuar = () => {
      const continuarBtn = Array.from(document.querySelectorAll('button')).find(
        btn => btn.textContent.trim().toLowerCase() === "continuar"
      );
      if (continuarBtn) {
        setTimeout(() => continuarBtn.click(), 300);
      } else {
        console.warn("Botón 'Continuar' no encontrado.");
      }
    };

    // Llenar dirección y número exterior
    setInputValue('input[name="address.address"]', "Ontario");
    setInputValue('input[name="address.ext_number"]', "1090");

    // Simular entrada real en el campo de código postal
    const cpInput = document.querySelector('input[name="address.postal_code"]');
    if (cpInput) {
      cpInput.focus();
      cpInput.value = "44820";
      cpInput.dispatchEvent(new Event("input", { bubbles: true }));
      cpInput.dispatchEvent(new KeyboardEvent("keydown", { key: "Tab", bubbles: true }));
      cpInput.dispatchEvent(new Event("blur", { bubbles: true }));
    }

    // Esperar a que el selector de colonia cargue correctamente
    const esperarColonia = (callback, intentos = 20) => {
      const intentar = () => {
        const selects = document.querySelectorAll('select.k-ds-body-02');
        const colonia = Array.from(selects).find(sel =>
          Array.from(sel.options).some(opt => opt.value === "2001")
        );
        if (colonia) {
          callback(colonia);
        } else if (intentos > 0) {
          setTimeout(() => intentar(--intentos), 250);
        } else {
          console.warn("Colonia no encontrada.");
        }
      };
      intentar();
    };

    // Selección fija de colonia por value
    esperarColonia((colonia) => {
      const opcion = Array.from(colonia.options).find(opt => opt.value === "2001");
      if (opcion) {
        opcion.selected = true;
        colonia.dispatchEvent(new Event("input", { bubbles: true }));
        colonia.dispatchEvent(new Event("change", { bubbles: true }));
        colonia.focus();
        colonia.blur(); // esto ayuda a cerrar validadores internos
      }
    });
    
    setTimeout(clickContinuar, 1600);
  });
});



document.getElementById("btnPaso3").addEventListener("click", () => {
  ejecutarPaso(() => {
    const setInputValue = (selector, value) => {
      const el = document.querySelector(selector);
      if (el) {
        el.value = value;
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
        el.dispatchEvent(new Event("blur", { bubbles: true }));
      }
    };

    const clickContinuar = () => {
      const continuarBtn = Array.from(document.querySelectorAll('button')).find(
        btn => btn.textContent.trim().toLowerCase() === "continuar"
      );
      if (continuarBtn) {
        setTimeout(() => continuarBtn.click(), 300);
      } else {
        console.warn("Botón 'Continuar' no encontrado.");
      }
    };

    // 1. Ingresos individual y familiar
    setInputValue('input[name="financial.monthly_salary"]', "12000");
    setInputValue('input[name="financial.family_salary"]', "18000");

    // 2. Seleccionar radio de "Sí" en "¿Te pagan por banco?"
    const bancoSi = document.querySelector('input[name="financial.is_salary_bank_deposit"][value="1"]');
    if (bancoSi) {
      bancoSi.click();
    }

    // 3. Seleccionar "Buena" en historial crediticio (value = "5")
    const selects = document.querySelectorAll('select.k-ds-body-02');
    const historial = Array.from(selects).find(sel =>
      Array.from(sel.options).some(opt => opt.value === "5")
    );

    if (historial) {
      const opcion = Array.from(historial.options).find(opt => opt.value === "5");
      if (opcion) {
        opcion.selected = true;
        historial.dispatchEvent(new Event("input", { bubbles: true }));
        historial.dispatchEvent(new Event("change", { bubbles: true }));
        historial.focus();
        historial.blur();
      }
    }
    setTimeout(clickContinuar, 1600);
  });
});

document.getElementById("btnPaso4").addEventListener("click", () => {
  ejecutarPaso(() => {
    // 1. Obtener el NIP desde el span con ID "token"
    const tokenSpan = document.querySelector("#token");
    const tokenMatch = tokenSpan?.textContent?.match(/\d{6}/);
    const nip = tokenMatch ? tokenMatch[0] : null;

    if (!nip) {
      console.warn("No se pudo obtener el NIP.");
      return;
    }

    // 2. Llenar los 6 campos del NIP
    for (let i = 0; i < 6; i++) {
      const input = document.querySelector(`#nip-input-${i}`);
      if (input) {
        input.value = nip[i];
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));
        input.dispatchEvent(new Event("blur", { bubbles: true }));
      }
    }

    // 3. Activar el checkbox de autorización
    const checkbox = document.querySelector('#authorization-checkbox');
    if (checkbox && !checkbox.checked) {
      checkbox.click(); // simula interacción real
    }

    // 4. Esperar hasta que el botón esté habilitado y hacer clic
    const esperarVerificar = (intentos = 20) => {
      const btn = document.querySelector('button[data-testid="btn-verify"]');
      if (btn && !btn.disabled) {
        btn.click();
      } else if (intentos > 0) {
        setTimeout(() => esperarVerificar(intentos - 1), 300);
      } else {
        console.warn("Botón de verificación no habilitado.");
      }
    };

    esperarVerificar();
  });
});
