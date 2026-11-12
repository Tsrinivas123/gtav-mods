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
  // 1. Mobile Navigation Hamburger Menu & Backdrop
  const hamburger = document.getElementById('hamburger');
  const navMenu = document.getElementById('navMenu');
  const navBackdrop = document.getElementById('navBackdrop');

  function closeMobileNav() {
    if (navMenu && navMenu.classList.contains('active')) {
      navMenu.classList.remove('active');
      if (navBackdrop) navBackdrop.classList.remove('active');
      document.body.classList.remove('nav-open');
      if (hamburger) {
        hamburger.setAttribute('aria-expanded', 'false');
        const icon = hamburger.querySelector('i');
        if (icon) icon.className = 'fa-solid fa-bars';
      }
    }
  }

  function openMobileNav() {
    if (navMenu) {
      navMenu.classList.add('active');
      if (navBackdrop) navBackdrop.classList.add('active');
      document.body.classList.add('nav-open');
      if (hamburger) {
        hamburger.setAttribute('aria-expanded', 'true');
        const icon = hamburger.querySelector('i');
        if (icon) icon.className = 'fa-solid fa-xmark';
      }
    }
  }

  if (hamburger && navMenu) {
    hamburger.addEventListener('click', () => {
      const isExpanded = navMenu.classList.contains('active');
      if (isExpanded) {
        closeMobileNav();
      } else {
        openMobileNav();
      }
    });

    if (navBackdrop) {
      navBackdrop.addEventListener('click', closeMobileNav);
    }

    navMenu.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', closeMobileNav);
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
      closeMobileNav();
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

  // 3.5. Newsletter Subscription Forms with Validation & Duplicate Prevention
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const newsletterForms = document.querySelectorAll('.newsletter-form');

  newsletterForms.forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const emailInput = form.querySelector('input[type="email"]');
      const submitBtn = form.querySelector('button[type="submit"]');
      
      if (!emailInput) return;
      
      const email = emailInput.value.trim();
      
      // Client-side validation
      if (!email) {
        window.showToast('Please enter your email address.', 'warning');
        emailInput.focus();
        return;
      }
      
      if (!emailRegex.test(email)) {
        window.showToast('Please enter a valid email address (e.g. name@example.com).', 'warning');
        emailInput.focus();
        return;
      }
      
      // Prevent duplicate submissions while request is processing
      if (form.dataset.submitting === 'true') {
        return;
      }
      form.dataset.submitting = 'true';
      
      // Visual pending state
      const originalBtnHtml = submitBtn ? submitBtn.innerHTML : '';
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
        submitBtn.style.opacity = '0.75';
        submitBtn.style.cursor = 'not-allowed';
      }
      if (emailInput) {
        emailInput.disabled = true;
      }
      
      try {
        const actionUrl = form.getAttribute('action') || '/newsletter/subscribe/';
        const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken') || '';
        
        const response = await fetch(actionUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
          },
          body: new URLSearchParams({ email: email })
        });
        
        const data = await response.json().catch(() => null);
        
        if (response.ok && data && data.success) {
          window.showToast(data.message || 'Subscribed to newsletter successfully!', 'success');
          form.reset();
        } else {
          const errorMsg = (data && data.message) ? data.message : 'Unable to subscribe. Please try again.';
          const toastType = (data && data.already_subscribed) ? 'info' : 'error';
          window.showToast(errorMsg, toastType);
        }
      } catch (err) {
        window.showToast('Network error while subscribing. Please check your connection.', 'error');
      } finally {
        form.dataset.submitting = 'false';
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalBtnHtml;
          submitBtn.style.opacity = '';
          submitBtn.style.cursor = '';
        }
        if (emailInput) {
          emailInput.disabled = false;
        }
      }
    });
  });

  // 3.6 Unconfigured Social Media Links Notification
  document.querySelectorAll('[data-social]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const social = btn.getAttribute('data-social');
      const href = btn.getAttribute('href');
      if (href === '#' || href === 'javascript:void(0)' || !href) {
        e.preventDefault();
        const name = social.charAt(0).toUpperCase() + social.slice(1);
        window.showToast(`${name} channel link has not been configured in site settings yet.`, 'info');
      }
    });
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

  // 6. Mini Cart Dropdown Management
  const miniCartDropdown = document.getElementById('miniCartDropdown');
  const headerCartWrapper = document.getElementById('headerCartWrapper');
  const cartIcon = document.getElementById('cartIcon');

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  window.renderMiniCart = function(data) {
    if (!data) return;
    const listEl = document.getElementById('miniCartItemsList');
    const totalEl = document.getElementById('miniCartSubtotalVal');
    const bottomEl = document.getElementById('miniCartBottomBox');
    const headerTotal = document.getElementById('headerCartTotal');
    const badge = document.getElementById('headerCartBadge');

    if (badge) {
      badge.innerText = data.cart_count || 0;
      badge.style.display = (data.cart_count > 0) ? 'inline-block' : 'none';
    }

    const totalText = data.cart_total_formatted || ('₹' + (data.cart_total || '0.00'));
    if (headerTotal) headerTotal.innerText = totalText;
    if (totalEl) totalEl.innerText = totalText;

    if (data.items && data.items.length > 0) {
      if (bottomEl) bottomEl.style.display = 'block';
      if (listEl) {
        listEl.innerHTML = data.items.map(item => `
          <div class="mini-cart-item" data-product-id="${item.id}">
            <div class="mini-cart-img-wrap">
              ${item.image ? `<img src="${item.image}" alt="${item.name}">` : `<div class="mini-cart-img-placeholder"><i class="fa-solid fa-box"></i></div>`}
            </div>
            <div class="mini-cart-info">
              <h4 class="mini-cart-title">${item.name}</h4>
              <span class="mini-cart-qty-price">${item.quantity} &times; ${item.price_formatted || ('₹' + item.price)}</span>
            </div>
            <button type="button" class="mini-cart-remove-btn" data-product-id="${item.id}" aria-label="Remove item" title="Remove item">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>
        `).join('');
      }
    } else {
      if (bottomEl) bottomEl.style.display = 'none';
      if (listEl) {
        listEl.innerHTML = `
          <div class="mini-cart-empty">
            <i class="fa-solid fa-cart-shopping" style="font-size: 1.6rem; color: #cbd5e1; margin-bottom: 8px;"></i>
            <p style="margin: 0; color: #64748b; font-size: 0.82rem; font-weight: 600;">Your cart is empty</p>
          </div>
        `;
      }
    }
  };

  window.openMiniCart = function() {
    if (miniCartDropdown) miniCartDropdown.classList.add('open');
  };

  window.closeMiniCart = function() {
    if (miniCartDropdown) miniCartDropdown.classList.remove('open');
  };

  if (cartIcon && miniCartDropdown) {
    cartIcon.addEventListener('click', (e) => {
      e.preventDefault();
      miniCartDropdown.classList.toggle('open');
    });
  }

  // Close when clicking outside
  document.addEventListener('click', (e) => {
    if (headerCartWrapper && !headerCartWrapper.contains(e.target)) {
      window.closeMiniCart();
    }
  });

  // Handle remove from mini-cart
  document.addEventListener('click', (e) => {
    const removeBtn = e.target.closest('.mini-cart-remove-btn');
    if (removeBtn) {
      e.preventDefault();
      const pid = removeBtn.getAttribute('data-product-id');
      const formData = new FormData();
      fetch(`/orders/cart/remove/${pid}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken') || '',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
      })
      .then(r => r.json())
      .then(data => {
        if (data.status === 'success') {
          window.renderMiniCart(data);
          if (window.showToast) window.showToast('Item removed from cart', 'info');
        }
      })
      .catch(err => console.error('Remove failure: ', err));
    }
  });
});
