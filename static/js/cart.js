/* ==========================================================================
   GTA MODS MARKETPLACE - SHOPPING CART ACTIONS & SUMS (cart.js)
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
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
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
        .then(res => res.json())
        .then(data => {
          if (data.status === 'success') {
            // Fade out and remove the card element
            card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            card.style.opacity = '0';
            card.style.transform = 'scale(0.9)';

            setTimeout(() => {
              card.remove();

              // Check if cart is empty, reload page to display empty state
              const remainingCards = document.querySelectorAll('.cart-card');
              if (remainingCards.length === 0) {
                window.location.reload();
              } else {
                // Update badge counts and recalculate totals
                const badges = document.querySelectorAll('.cart-badge');
                badges.forEach(b => b.innerText = data.cart_count);

                // Recalculate summary details
                recalculateCartSummary();
              }
            }, 400);
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
    const unitPrice = parseFloat(itemPriceText.getAttribute('data-unit-price'));

    decBtn.addEventListener('click', () => {
      let currentVal = parseInt(qtyInput.value);
      if (currentVal > 1) {
        qtyInput.value = currentVal - 1;
        updateQtyOnServer(product_id, qtyInput.value, unitPrice, itemPriceText);
      }
    });

    incBtn.addEventListener('click', () => {
      let currentVal = parseInt(qtyInput.value);
      qtyInput.value = currentVal + 1;
      updateQtyOnServer(product_id, qtyInput.value, unitPrice, itemPriceText);
    });
  });

  // Update quantity on server via AJAX
  function updateQtyOnServer(productId, quantity, unitPrice, priceTextElement) {
    const formData = new FormData();
    formData.append('quantity', quantity);

    const url = `/orders/cart/update/${productId}/`;

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
          // Update product card total on client-side
          const lineTotal = (unitPrice * parseInt(quantity)).toFixed(2);
          priceTextElement.innerText = `₹${lineTotal}`;

          // Recalculate global totals
          recalculateCartSummary();
        }
      })
      .catch(err => console.error('Qty update error: ', err));
  }

  // 3. Recalculate Global Cart Summary Totals
  function recalculateCartSummary() {
    let subtotal = 0;

    // Accumulate from all active cart cards
    const cartCards = document.querySelectorAll('.cart-card');
    cartCards.forEach(card => {
      const p_id = card.id.replace('cartCard-', '');
      const priceText = document.getElementById(`itemPrice-${p_id}`);
      if (priceText) {
        subtotal += parseFloat(priceText.innerText.replace('₹', ''));
      }
    });

    const subtotalLabel = document.getElementById('summarySubtotal');
    if (subtotalLabel) subtotalLabel.innerText = `₹${subtotal.toFixed(2)}`;

    // Discount
    let discount = 0;
    const discountLabel = document.getElementById('summaryDiscount');
    const discountPercentageAttr = discountLabel ? discountLabel.getAttribute('data-discount-percentage') : 0;

    if (discountLabel && discountPercentageAttr > 0) {
      discount = subtotal * (parseFloat(discountPercentageAttr) / 100.0);
      discountLabel.innerText = `-₹${discount.toFixed(2)}`;
    }

    const afterDiscount = Math.max(0, subtotal - discount);

    // Grand Total
    const grandTotal = afterDiscount;
    const grandTotalLabel = document.getElementById('summaryGrandTotal');
    if (grandTotalLabel) grandTotalLabel.innerText = `₹${grandTotal.toFixed(2)}`;
  }
});
