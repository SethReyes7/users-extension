async function ejecutarFuncion(nombreFuncion) {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: (funcName) => {
      if (typeof window[funcName] === "function") {
        window[funcName]();
      } else {
        alert("No se encontró la función: " + funcName);
      }
    },
    args: [nombreFuncion]
  });
}

document.getElementById("btnPaso1").addEventListener("click", () => ejecutarFuncion("llenarPaso1"));
document.getElementById("btnPaso2").addEventListener("click", () => ejecutarFuncion("llenarPaso2"));
document.getElementById("btnPaso3").addEventListener("click", () => ejecutarFuncion("llenarPaso3"));
