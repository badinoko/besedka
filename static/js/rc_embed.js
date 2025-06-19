/* Rocket.Chat iframe integration v2 */
(function() {
  function initRC() {
    console.log('🚀 Initializing Rocket.Chat iframe...');
    var container = document.getElementById('rocketchat-container');
    if (!container) {
      console.error('❌ rocketchat-container not found!');
      return;
    }

    console.log('✅ Container found, creating iframe...');
    var iframe = document.createElement('iframe');
    iframe.src = 'http://127.0.0.1:3000/';  // Прямое подключение к Rocket.Chat
    iframe.style.border = '0';
    iframe.style.width = '100%';
    iframe.style.height = '100%';
    iframe.setAttribute('allow', 'clipboard-write; microphone; camera');
    iframe.setAttribute('allowfullscreen', 'true');

    container.appendChild(iframe);
    console.log('✅ Rocket.Chat iframe added successfully!');
  }

  document.addEventListener('DOMContentLoaded', initRC);
  // Также попробуем сразу, если DOM уже готов
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRC);
  } else {
    initRC();
  }
})();
