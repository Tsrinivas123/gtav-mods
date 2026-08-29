/* ==========================================================================
   GTA MODS MARKETPLACE - PRODUCT DETAIL PAGES INTERACTIVITY (product.js)
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Screenshot Gallery Thumbnail Switcher
  const mainImg = document.getElementById('mainGalleryImg');
  const thumbs = document.querySelectorAll('.gallery-thumb');

  if (mainImg && thumbs.length > 0) {
    thumbs.forEach(thumb => {
      thumb.addEventListener('click', () => {
        // Remove active class from all
        thumbs.forEach(t => t.classList.remove('active'));
        
        // Add active to current
        thumb.classList.add('active');
        
        // Swap image src
        const newSrc = thumb.querySelector('img').src;
        mainImg.src = newSrc;
        
        // Add zoom anim class
        mainImg.style.animation = 'none';
        setTimeout(() => {
          mainImg.style.animation = 'fadeUp 0.3s ease forwards';
        }, 10);
      });
    });
  }

  // 2. Tab Navigation Selector
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');

  if (tabBtns.length > 0 && tabContents.length > 0) {
    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const tabTarget = btn.getAttribute('data-tab');
        
        // Deactivate all buttons & contents
        tabBtns.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));
        
        // Activate target elements
        btn.classList.add('active');
        const targetContent = document.getElementById(tabTarget);
        if (targetContent) targetContent.classList.add('active');
      });
    });
  }

  // 3. Copy Install Script / Commands Clipboard
  const copyBtn = document.getElementById('copyBtn');
  const commandText = document.getElementById('commandText');

  if (copyBtn && commandText) {
    copyBtn.addEventListener('click', () => {
      const code = commandText.innerText;
      navigator.clipboard.writeText(code).then(() => {
        const oldClass = copyBtn.className;
        copyBtn.className = 'fa-solid fa-check';
        copyBtn.style.color = 'var(--color-success)';
        
        setTimeout(() => {
          copyBtn.className = oldClass;
          copyBtn.style.color = '';
        }, 2000);
      }).catch(err => {
        console.error('Failed to copy text: ', err);
      });
    });
  }

  // Helper to extract CSRF token from page
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

  // 4. AJAX Add to Cart
  const addCartBtn = document.getElementById('ajaxAddToCartBtn');
  if (addCartBtn) {
    addCartBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const product_id = addCartBtn.getAttribute('data-product-id');
      const quantity = document.getElementById('productQtyInput') ? document.getElementById('productQtyInput').value : 1;
      
      const formData = new FormData();
      formData.append('quantity', quantity);

      const url = `/orders/cart/add/${product_id}/`;
      
      fetch(url, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
      })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          // Update cart badge counts
          const badges = document.querySelectorAll('.cart-badge');
          badges.forEach(b => b.innerText = data.cart_count);
          
          // Flash message notification
          const flash = document.createElement('div');
          flash.style.cssText = 'position: fixed; top: 90px; right: 5%; z-index: 9999; background: var(--card-bg); border-left: 4px solid var(--color-success); border-radius: 4px; padding: 15px 20px; box-shadow: var(--shadow-soft); display: flex; align-items: center; gap: 12px; font-size: 0.85rem;';
          flash.innerHTML = `<i class="fa-solid fa-circle-check" style="color: var(--color-success); font-size: 1.1rem;"></i> <span>${data.message}</span>`;
          document.body.appendChild(flash);
          
          setTimeout(() => {
            flash.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-20px)';
            setTimeout(() => flash.remove(), 600);
          }, 3000);
        }
      })
      .catch(err => console.error('Cart operation failure: ', err));
    });
  }

  // 5. AJAX Wishlist Toggle
  const wishlistBtn = document.getElementById('wishlistToggleBtn');
  if (wishlistBtn) {
    wishlistBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const product_id = wishlistBtn.getAttribute('data-product-id');
      const url = `/accounts/wishlist/toggle/${product_id}/`;
      
      fetch(url, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          const heart = wishlistBtn.querySelector('i');
          const span = wishlistBtn.querySelector('span');
          
          if (data.added) {
            heart.className = 'fa-solid fa-heart';
            heart.style.color = 'var(--accent-orange)';
            if (span) span.innerText = 'Wishlisted';
          } else {
            heart.className = 'fa-regular fa-heart';
            heart.style.color = '';
            if (span) span.innerText = 'Add to Wishlist';
          }
          
          // Flash message notification
          const flash = document.createElement('div');
          flash.style.cssText = 'position: fixed; top: 90px; right: 5%; z-index: 9999; background: var(--card-bg); border-left: 4px solid var(--accent-orange); border-radius: 4px; padding: 15px 20px; box-shadow: var(--shadow-soft); display: flex; align-items: center; gap: 12px; font-size: 0.85rem;';
          flash.innerHTML = `<i class="fa-solid fa-circle-check" style="color: var(--accent-orange); font-size: 1.1rem;"></i> <span>${data.message}</span>`;
          document.body.appendChild(flash);
          
          setTimeout(() => {
            flash.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-20px)';
            setTimeout(() => flash.remove(), 600);
          }, 3000);
        }
      })
      .catch(err => console.error('Wishlist operation failure: ', err));
    });
  }
});
