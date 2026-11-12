/* ==========================================================================
   GTA MODS MARKETPLACE - STORE FILTERS & LAYOUT TOGGLE (store.js)
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // 0. Mobile Filter Toggle Drawer Handler
  const mobileToggleBtn = document.getElementById('toggleMobileFilters');
  const filterSidebar = document.querySelector('.filter-sidebar');

  if (mobileToggleBtn && filterSidebar) {
    mobileToggleBtn.addEventListener('click', () => {
      const isActive = filterSidebar.classList.toggle('active-mobile');
      mobileToggleBtn.setAttribute('aria-expanded', isActive ? 'true' : 'false');
      const icon = mobileToggleBtn.querySelector('.fa-chevron-down, .fa-chevron-up');
      if (icon) {
        icon.className = isActive ? 'fa-solid fa-chevron-up' : 'fa-solid fa-chevron-down';
      }
    });
  }

  // 1. Grid/List Layout Toggle
  const gridBtn = document.getElementById('gridBtn');
  const listBtn = document.getElementById('listBtn');
  const modsGrid = document.getElementById('modsGrid');

  if (gridBtn && listBtn && modsGrid) {
    // Restore layout preference from localStorage
    const savedLayout = localStorage.getItem('storeLayout') || 'grid';
    
    if (savedLayout === 'list') {
      modsGrid.classList.add('list');
      listBtn.classList.add('active');
      gridBtn.classList.remove('active');
    } else {
      modsGrid.classList.remove('list');
      gridBtn.classList.add('active');
      listBtn.classList.remove('active');
    }

    gridBtn.addEventListener('click', () => {
      modsGrid.classList.remove('list');
      gridBtn.classList.add('active');
      listBtn.classList.remove('active');
      localStorage.setItem('storeLayout', 'grid');
    });

    listBtn.addEventListener('click', () => {
      modsGrid.classList.add('list');
      listBtn.classList.add('active');
      gridBtn.classList.remove('active');
      localStorage.setItem('storeLayout', 'list');
    });
  }

  // 2. Price Range Slider Synchronization & Dynamic Gradient Fill
  const minPriceInput = document.getElementById('minPriceInput');
  const maxPriceInput = document.getElementById('maxPriceInput');
  const priceSlider = document.getElementById('priceRangeSlider');
  const priceBadge = document.getElementById('priceRangeBadge');

  const updateSliderFill = (slider, val) => {
    if (!slider) return;
    const min = parseFloat(slider.min) || 0;
    const max = parseFloat(slider.max) || 3000;
    const current = parseFloat(val) || max;
    const percentage = Math.max(0, Math.min(100, ((current - min) / (max - min)) * 100));
    slider.style.background = `linear-gradient(to right, #ff6b00 0%, #ff6b00 ${percentage}%, #e2e8f0 ${percentage}%, #e2e8f0 100%)`;
  };

  if (priceSlider && minPriceInput && maxPriceInput) {
    const updateBadge = (val) => {
      if (priceBadge) priceBadge.textContent = 'Max: ₹' + (val || '3000');
    };

    // Initialize fill on load
    updateSliderFill(priceSlider, priceSlider.value);

    priceSlider.addEventListener('input', (e) => {
      const val = e.target.value;
      maxPriceInput.value = val;
      updateBadge(val);
      updateSliderFill(priceSlider, val);
    });

    // Auto submit on release of slider
    priceSlider.addEventListener('change', () => {
      if (filterForm) filterForm.submit();
    });

    maxPriceInput.addEventListener('input', (e) => {
      const val = e.target.value;
      if (val !== '') {
        priceSlider.value = val;
        updateSliderFill(priceSlider, val);
      }
      updateBadge(val);
    });

    // Pressing Enter in price inputs submits form
    [minPriceInput, maxPriceInput].forEach(inp => {
      inp.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          if (filterForm) filterForm.submit();
        }
      });
    });
  }

  // 3. Clear Filters Handler
  const filterForm = document.getElementById('filterForm');
  const clearBtn = document.getElementById('clearFiltersBtn');

  if (clearBtn && filterForm) {
    clearBtn.addEventListener('click', () => {
      const searchBox = filterForm.querySelector('input[name="search"]');
      if (searchBox) searchBox.value = '';

      const checkboxes = filterForm.querySelectorAll('input[type="checkbox"]');
      checkboxes.forEach(cb => cb.checked = false);

      if (minPriceInput) minPriceInput.value = '';
      if (maxPriceInput) maxPriceInput.value = '';
      if (priceSlider) {
        priceSlider.value = priceSlider.max || '3000';
        updateSliderFill(priceSlider, priceSlider.value);
      }
      if (priceBadge) priceBadge.textContent = 'Max: ₹' + (priceSlider?.max || '3000');

      const selectFields = filterForm.querySelectorAll('select');
      selectFields.forEach(select => select.selectedIndex = 0);

      const sortByHidden = document.getElementById('sortByHiddenInput');
      if (sortByHidden) sortByHidden.value = 'newest';

      filterForm.submit();
    });
  }

  // 4. Live Filtering Checkbox Autosubmit
  const autosubmitCheckboxes = document.querySelectorAll('.autosubmit-filter');
  autosubmitCheckboxes.forEach(cb => {
    cb.addEventListener('change', () => {
      if (filterForm) filterForm.submit();
    });
  });

  // 5. Sort By Dropdown Change Handler
  const sortBySelect = document.getElementById('sortBySelect');
  const sortByHidden = document.getElementById('sortByHiddenInput');
  if (sortBySelect && filterForm) {
    sortBySelect.addEventListener('change', () => {
      if (sortByHidden) {
        sortByHidden.value = sortBySelect.value;
      }
      filterForm.submit();
    });
  }
});
