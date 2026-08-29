/* ==========================================================================
   GTA MODS MARKETPLACE - GLOBAL JAVASCRIPT & PARTICLES CANVAS (main.js)
   ========================================================================== */

// Global Accessible Toast Notification API
window.showToast = function(message, type = 'info', duration = 4000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const icons = {
    success: 'fa-circle-check',
    error: 'fa-circle-xmark',
    warning: 'fa-circle-exclamation',
    info: 'fa-circle-info'
  };

  const toast = document.createElement('div');
  toast.className = `toast-item toast-${type}`;
  toast.setAttribute('role', 'status');
  toast.setAttribute('aria-live', 'polite');

  const iconClass = icons[type] || icons.info;
  toast.innerHTML = `
    <div class="toast-icon"><i class="fa-solid ${iconClass}"></i></div>
    <div class="toast-content">${message}</div>
    <button class="toast-close" aria-label="Close notification">&times;</button>
    <div class="toast-progress-bar"></div>
  `;

  container.appendChild(toast);

  // Entrance animation frame
  requestAnimationFrame(() => {
    toast.classList.add('visible');
  });

  const progressBar = toast.querySelector('.toast-progress-bar');
  if (progressBar) {
    progressBar.style.transition = `transform ${duration}ms linear`;
    requestAnimationFrame(() => {
      progressBar.style.transform = 'scaleX(0)';
    });
  }

  const dismiss = () => {
    toast.classList.remove('visible');
    toast.classList.add('dismissed');
    setTimeout(() => {
      if (toast.parentNode) toast.remove();
    }, 400);
  };

  const timer = setTimeout(dismiss, duration);

  const closeBtn = toast.querySelector('.toast-close');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      clearTimeout(timer);
      dismiss();
    });
  }
};

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Navigation Hamburger Menu
  const hamburger = document.getElementById('hamburger');
  const navMenu = document.getElementById('navMenu');

  if (hamburger && navMenu) {
    hamburger.addEventListener('click', () => {
      const isExpanded = navMenu.classList.toggle('active');
      hamburger.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
      const icon = hamburger.querySelector('i');
      if (icon) {
        icon.className = isExpanded ? 'fa-solid fa-xmark' : 'fa-solid fa-bars';
      }
    });
  }

  // 2. Dynamic Scroll Class for Header
  const header = document.querySelector('header');
  if (header) {
    let ticking = false;
    window.addEventListener('scroll', () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          if (window.scrollY > 50) {
            header.classList.add('scrolled');
          } else {
            header.classList.remove('scrolled');
          }
          ticking = false;
        });
        ticking = true;
      }
    });
  }

  // 2.5 User Account Dropdown Click Trigger
  const profileDropdown = document.querySelector('.header-profile-dropdown');
  const profileTrigger = document.querySelector('.profile-trigger');

  if (profileDropdown && profileTrigger) {
    profileTrigger.addEventListener('click', (e) => {
      e.stopPropagation();
      const isActive = profileDropdown.classList.toggle('active');
      profileTrigger.setAttribute('aria-expanded', isActive ? 'true' : 'false');
    });

    document.addEventListener('click', (e) => {
      if (!profileDropdown.contains(e.target)) {
        profileDropdown.classList.remove('active');
        profileTrigger.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // Global Escape key listener for open menus and modals
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (navMenu && navMenu.classList.contains('active')) {
        navMenu.classList.remove('active');
        if (hamburger) {
          hamburger.setAttribute('aria-expanded', 'false');
          const icon = hamburger.querySelector('i');
          if (icon) icon.className = 'fa-solid fa-bars';
        }
      }
      if (profileDropdown && profileDropdown.classList.contains('active')) {
        profileDropdown.classList.remove('active');
        if (profileTrigger) profileTrigger.setAttribute('aria-expanded', 'false');
      }
    }
  });

  // 3. Auto-Dismiss Django Flash Messages & Convert to Toasts if present
  const flashMessages = document.querySelectorAll('.flash-msg-data');
  flashMessages.forEach(msgEl => {
    const text = msgEl.getAttribute('data-message');
    const tags = msgEl.getAttribute('data-tags') || 'info';
    let type = 'info';
    if (tags.includes('error') || tags.includes('danger')) type = 'error';
    else if (tags.includes('success')) type = 'success';
    else if (tags.includes('warning')) type = 'warning';
    
    if (text) {
      window.showToast(text, type);
    }
  });

  // 4. Background Particle Network Canvas (Optimized for performance & battery)
  const canvas = document.getElementById('bg-particles');
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (canvas && !prefersReducedMotion) {
    const ctx = canvas.getContext('2d');
    let particlesArray = [];
    const colors = ['#ff6b00', '#00e5ff', '#3f3f46'];
    let animId = null;
    let isTabActive = true;

    function setSize() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }
    setSize();

    class Particle {
      constructor() {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.size = Math.random() * 2 + 1;
        this.speedX = Math.random() * 0.4 - 0.2;
        this.speedY = Math.random() * 0.4 - 0.2;
        this.color = colors[Math.floor(Math.random() * colors.length)];
      }

      update() {
        this.x += this.speedX;
        this.y += this.speedY;

        if (this.x < 0 || this.x > canvas.width) this.speedX = -this.speedX;
        if (this.y < 0 || this.y > canvas.height) this.speedY = -this.speedY;
      }

      draw() {
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    function init() {
      const isMobile = window.innerWidth < 768;
      const densityDivider = isMobile ? 45000 : 18000;
      const quantity = Math.max(10, Math.floor((canvas.width * canvas.height) / densityDivider));
      particlesArray = [];
      for (let i = 0; i < quantity; i++) {
        particlesArray.push(new Particle());
      }
    }
    init();

    let resizeTimeout;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        setSize();
        init();
      }, 200);
    });

    function connectParticles() {
      const isMobile = window.innerWidth < 768;
      if (isMobile) return; // Skip line calculation on mobile for extra CPU/GPU performance

      const maxDistance = 110;
      for (let a = 0; a < particlesArray.length; a++) {
        for (let b = a; b < particlesArray.length; b++) {
          const dx = particlesArray[a].x - particlesArray[b].x;
          const dy = particlesArray[a].y - particlesArray[b].y;
          const distance = Math.sqrt(dx * dx + dy * dy);

          if (distance < maxDistance) {
            const alpha = (1 - (distance / maxDistance)) * 0.12;
            ctx.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
            ctx.lineWidth = 0.5;
            ctx.beginPath();
            ctx.moveTo(particlesArray[a].x, particlesArray[a].y);
            ctx.lineTo(particlesArray[b].x, particlesArray[b].y);
            ctx.stroke();
          }
        }
      }
    }

    function animate() {
      if (!isTabActive) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (let i = 0; i < particlesArray.length; i++) {
        particlesArray[i].update();
        particlesArray[i].draw();
      }
      connectParticles();
      animId = requestAnimationFrame(animate);
    }

    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        isTabActive = false;
        if (animId) cancelAnimationFrame(animId);
      } else {
        isTabActive = true;
        animate();
      }
    });

    animate();
  }
});
