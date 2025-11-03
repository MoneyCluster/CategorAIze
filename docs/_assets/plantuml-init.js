// PlantUML renderer - using txt encoding with proper UTF-8 handling
(function() {
  'use strict';

  // Convert string to UTF-8 bytes properly
  function stringToUtf8Bytes(str) {
    const bytes = [];
    for (let i = 0; i < str.length; i++) {
      let charCode = str.charCodeAt(i);
      if (charCode < 0x80) {
        bytes.push(charCode);
      } else if (charCode < 0x800) {
        bytes.push(0xC0 | (charCode >> 6));
        bytes.push(0x80 | (charCode & 0x3F));
      } else if ((charCode & 0xFC00) === 0xD800 && i + 1 < str.length && (str.charCodeAt(i + 1) & 0xFC00) === 0xDC00) {
        // Surrogate pair
        charCode = 0x10000 + (((charCode & 0x03FF) << 10) | (str.charCodeAt(++i) & 0x03FF));
        bytes.push(0xF0 | (charCode >> 18));
        bytes.push(0x80 | ((charCode >> 12) & 0x3F));
        bytes.push(0x80 | ((charCode >> 6) & 0x3F));
        bytes.push(0x80 | (charCode & 0x3F));
      } else {
        bytes.push(0xE0 | (charCode >> 12));
        bytes.push(0x80 | ((charCode >> 6) & 0x3F));
        bytes.push(0x80 | (charCode & 0x3F));
      }
    }
    return bytes;
  }

  // Base64 encode with PlantUML character substitution
  function base64Encode(bytes) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
    let result = '';
    let i = 0;
    
    while (i < bytes.length) {
      const a = bytes[i++] || 0;
      const b = bytes[i++] || 0;
      const c = bytes[i++] || 0;
      
      const bitmap = (a << 16) | (b << 8) | c;
      
      result += chars.charAt((bitmap >> 18) & 63);
      result += chars.charAt((bitmap >> 12) & 63);
      result += i - 2 < bytes.length ? chars.charAt((bitmap >> 6) & 63) : '';
      result += i - 1 < bytes.length ? chars.charAt(bitmap & 63) : '';
    }
    
    // PlantUML encoding: + -> -, / -> _, remove padding =
    return result.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }

  function encodePlantUMLTxt(text) {
    // Convert to UTF-8 bytes and encode
    const bytes = stringToUtf8Bytes(text);
    return base64Encode(bytes);
  }

  function renderPlantUMLDiagrams() {
    // Try multiple selectors to find PlantUML blocks
    const selectors = [
      'code.language-plantuml',
      'code.language-puml',
      'pre code.plantuml',
      'pre.plantuml code',
      'pre code.language-plantuml',
      'pre code.language-puml'
    ];
    
    const plantumlBlocks = new Set();
    selectors.forEach(selector => {
      document.querySelectorAll(selector).forEach(el => plantumlBlocks.add(el));
    });
    
    if (plantumlBlocks.size === 0) {
      console.log('No PlantUML blocks found');
      return;
    }
    
    console.log(`Found ${plantumlBlocks.size} PlantUML blocks`);

    plantumlBlocks.forEach((block) => {
      const pre = block.closest('pre');
      if (!pre || pre.dataset.plantumlProcessed) return;
      pre.dataset.plantumlProcessed = 'true';
      
      let plantumlCode = block.textContent || block.innerText || '';
      if (!plantumlCode.trim()) return;
      
      // Clean and ensure tags
      plantumlCode = plantumlCode.trim();
      if (!plantumlCode.includes('@startuml')) {
        plantumlCode = '@startuml\n' + plantumlCode;
      }
      if (!plantumlCode.includes('@enduml')) {
        plantumlCode = plantumlCode + '\n@enduml';
      }
      
      // Create container
      const container = document.createElement('div');
      container.className = 'plantuml-diagram';
      
      const placeholder = document.createElement('div');
      placeholder.className = 'plantuml-loading';
      placeholder.textContent = 'Загрузка диаграммы...';
      container.appendChild(placeholder);
      
      pre.parentNode.replaceChild(container, pre);
      
      try {
        // Use txt encoding
        const encoded = encodePlantUMLTxt(plantumlCode);
        const url = `https://www.plantuml.com/plantuml/svg/txt/${encoded}`;
        
        const img = document.createElement('img');
        img.src = url;
        img.alt = 'PlantUML Diagram';
        img.style.cssText = 'max-width: 100%; height: auto;';
        
        img.onload = () => {
          placeholder.remove();
          container.appendChild(img);
        };
        
        img.onerror = (e) => {
          console.error('PlantUML load error:', e, 'URL length:', url.length);
          placeholder.innerHTML = '<strong>Ошибка загрузки диаграммы</strong><br><small>Проверьте синтаксис PlantUML или попробуйте позже</small>';
          placeholder.style.color = '#d32f2f';
        };
      } catch (e) {
        placeholder.innerHTML = '<strong>Ошибка обработки диаграммы</strong><br><small>' + e.message + '</small>';
        placeholder.style.color = '#d32f2f';
        console.error('PlantUML encoding error:', e);
      }
    });
  }

  // Wait for DOM and execute
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderPlantUMLDiagrams);
  } else {
    // Small delay to ensure all scripts are loaded
    setTimeout(renderPlantUMLDiagrams, 100);
  }
})();
