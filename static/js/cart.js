/* ==========================================================================
   GTA MODS MARKETPLACE - SHOPPING CART ACTIONS & SUMS (cart.js)
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // Helper to extract CSRF token from page or cookies
  function getCSRFToken() {
    const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (input && input.value) return input.value;
    
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, 10) === 'csrftoken=') {
          cookieValue = decodeURIComponent(cookie.substring(10));
          break;
        }
      }
    }
    return cookieValue || '';
  }

  // 1. AJAX Remove Item from Cart
  const removeBtns = document.querySelectorAll('.cart-card-remove');
  removeBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const product_id = btn.getAttribute('data-product-id');
      const card = document.getElementById(`cartCard-${product_id}`);

      const url = `/orders/cart/remove/${product_id}/`;

      fetch(url, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCSRFToken(),
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
        .then(res => res.json())
        .then(data => {
          if (data.status === 'success') {
            if (card) {
              card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
              card.style.opacity = '0';
              card.style.transform = 'scale(0.9)';

              setTimeout(() => {
                card.remove();
                const remainingCards = document.querySelectorAll('.cart-card');
                if (remainingCards.length === 0) {
                  window.location.reload();
                } else {
                  document.querySelectorAll('.cart-badge').forEach(b => b.innerText = data.cart_count);
                  const hTotal = document.getElementById('headerCartTotal');
                  if (hTotal && data.cart_total_formatted) hTotal.innerText = data.cart_total_formatted;
                  recalculateCartSummary();
                }
              }, 300);
            }
          }
        })
        .catch(err => console.error('Remove operation failed: ', err));
    });
  });

  // 2. Quantity Selectors Increase / Decrease
  const qtyWrappers = document.querySelectorAll('.cart-card-qty');
  qtyWrappers.forEach(wrap => {
    const decBtn = wrap.querySelector('.qty-btn.minus');
    const incBtn = wrap.querySelector('.qty-btn.plus');
    const qtyInput = wrap.querySelector('.qty-input');
    const product_id = wrap.getAttribute('data-product-id');
    const itemPriceText = document.getElementById(`itemPrice-${product_id}`);
    const unitPrice = parseFloat(itemPriceText ? itemPriceText.getAttribute('data-unit-price') : 0) || 0;

    let updateTimeout = null;

    function applyQtyChange(newVal) {
      if (newVal < 1) newVal = 1;
      qtyInput.value = newVal;

      // 1. INSTANT client-side UI update (zero delay!)
      if (itemPriceText && unitPrice > 0) {
        const lineTotal = (unitPrice * newVal).toFixed(2);
        itemPriceText.innerText = `₹${lineTotal}`;
      }
      recalculateCartSummary();

      // 2. Debounced background sync with server
      if (updateTimeout) clearTimeout(updateTimeout);
      updateTimeout = setTimeout(() => {
        syncQtyWithServer(product_id, newVal);
      }, 300);
    }

    if (decBtn) {
      decBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        let currentVal = parseInt(qtyInput.value, 10) || 1;
        if (currentVal > 1) {
          applyQtyChange(currentVal - 1);
        }
      });
    }

    if (incBtn) {
      incBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        let currentVal = parseInt(qtyInput.value, 10) || 1;
        applyQtyChange(currentVal + 1);
      });
    }
  });

  // Sync quantity with server via AJAX
  function syncQtyWithServer(productId, quantity) {
    const formData = new FormData();
    formData.append('quantity', quantity);

    const url = `/orders/cart/update/${productId}/`;

    fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCSRFToken(),
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: formData
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          if (data.cart_count !== undefined) {
            document.querySelectorAll('.cart-badge').forEach(b => {
              b.innerText = data.cart_count;
              b.style.display = data.cart_count > 0 ? 'flex' : 'none';
            });
          }
          if (data.cart_total_formatted) {
            const hTotal = document.getElementById('headerCartTotal');
            if (hTotal) hTotal.innerText = data.cart_total_formatted;
          }
        }
      })
      .catch(err => console.error('Qty update error: ', err));
  }

  // 3. Recalculate Global Cart Summary Totals
  function recalculateCartSummary() {
    let subtotal = 0;

    const cartCards = document.querySelectorAll('.cart-card');
    cartCards.forEach(card => {
      const p_id = card.id.replace('cartCard-', '');
      const priceText = document.getElementById(`itemPrice-${p_id}`);
      if (priceText) {
        const val = parseFloat(priceText.innerText.replace(/[₹$,]/g, '')) || 0;
        subtotal += val;
      }
    });

    const subtotalLabel = document.getElementById('summarySubtotal');
    if (subtotalLabel) subtotalLabel.innerText = `₹${subtotal.toFixed(2)}`;

    // Discount
    let discount = 0;
    const discountLabel = document.getElementById('summaryDiscount');
    const discountPercentageAttr = discountLabel ? discountLabel.getAttribute('data-discount-percentage') : 0;

    if (discountLabel && parseFloat(discountPercentageAttr) > 0) {
      discount = subtotal * (parseFloat(discountPercentageAttr) / 100.0);
      discountLabel.innerText = `-₹${discount.toFixed(2)}`;
    }

    const grandTotal = Math.max(0, subtotal - discount);
    const grandTotalLabel = document.getElementById('summaryGrandTotal');
    if (grandTotalLabel) grandTotalLabel.innerText = `₹${grandTotal.toFixed(2)}`;
  }
});
