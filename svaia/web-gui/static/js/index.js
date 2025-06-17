

async function fetchData(content) {
  try {
    const response = await fetch('http://localhost:4446/chat/answer', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_msg: content
      })
    });
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error:', error);
    return { message: "No se ha podido enviar una respuesta" };
  }
}


document.addEventListener("DOMContentLoaded", function() {
  const chatContainer = document.getElementById("contenedor-mensajes");


  const mensaje = document.createElement("div");
  mensaje.classList.add("d-flex", "align-items-center", "my-3");

  const icono = document.createElement("i");
  icono.classList.add("bi", "bi-robot", "me-4");
  mensaje.appendChild(icono);


  const texto = document.createElement("div");
  texto.classList.add("mensaje_bot");
  texto.textContent = "¡Hola! Soy un bot, ¿en qué puedo ayudarte?";
  mensaje.appendChild(texto);


  chatContainer.appendChild(mensaje);

  //Hasta aquí llega la funcionalidad de "BIENVENIDA"

  const boton_enviar = document.getElementById("boton_enviar");
  const texto_input= document.getElementById("formulario");

  boton_enviar.addEventListener("click", function(){

      const contenido = texto_input.value;
      if (contenido ==="") return;

  

      const mensaje = document.createElement("div");
      mensaje.classList.add("d-flex", "align-items-center", "my-3");
      const texto = document.createElement("div");
      texto.classList.add("mensaje_user","me-4");
      texto.textContent = contenido;
      mensaje.appendChild(texto);
      const icono = document.createElement("i");
      icono.classList.add("bi", "bi-person-fill");
      mensaje.appendChild(icono);
      chatContainer.appendChild(mensaje);

      texto_input.value="";
      
  // Realizar la petición POST al servidor


      // Crear y mostrar el mensaje del bot
      const mensaje_respuesta = document.createElement("div");
      mensaje_respuesta.classList.add("d-flex", "align-items-center", "my-3");

      const icono_respuesta = document.createElement("i");
      icono_respuesta.classList.add("bi", "bi-robot", "me-4");
      mensaje_respuesta.appendChild(icono_respuesta);

      const texto_respuesta = document.createElement("div");
      texto_respuesta.classList.add("mensaje_bot");
      //fetchData(contenido).then(data=> texto_respuesta.textContent = data.message);
      fetchData(contenido).then(data => texto_respuesta.textContent = data.response);
      mensaje_respuesta.appendChild(texto_respuesta);

      chatContainer.appendChild(mensaje_respuesta);
  
  });
});
