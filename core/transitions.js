// =============================
//  LOESCH & ORÁCULO | TRANSITIONS CORE
//  Núcleo de Transição Oracular entre Portais
// =============================

document.addEventListener("DOMContentLoaded", () => {
  const links = document.querySelectorAll("a[data-portal]");
  const fadeOverlay = createFadeOverlay();

  links.forEach(link => {
    link.addEventListener("click", event => {
      event.preventDefault();
      const destino = link.getAttribute("href");
      const portal = link.dataset.portal;

      // Inicia transição com fade suave
      iniciarTransicao(portal, destino);
    });
  });

  function createFadeOverlay() {
    const overlay = document.createElement("div");
    overlay.id = "fadeOverlay";
    overlay.style.position = "fixed";
    overlay.style.top = 0;
    overlay.style.left = 0;
    overlay.style.width = "100%";
    overlay.style.height = "100%";
    overlay.style.backgroundColor = "#000";
    overlay.style.opacity = 0;
    overlay.style.pointerEvents = "none";
    overlay.style.transition = "opacity 0.8s ease-in-out";
    document.body.appendChild(overlay);
    return overlay;
  }

  function iniciarTransicao(portal, destino) {
    const overlay = document.getElementById("fadeOverlay");

    // Ativa a camada de transição
    overlay.style.pointerEvents = "auto";
    overlay.style.opacity = 1;

    // Breve delay para o fade completar antes da navegação
    setTimeout(() => {
      window.location.href = destino;
    }, 800);

    // (Opcional) log simbólico no console
    console.log(`🜂 Travessia iniciada: ${portal.toUpperCase()} → ${destino}`);
  }
});
