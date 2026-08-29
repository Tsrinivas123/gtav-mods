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

  // 2. Price Range Slider Synchronization
  const minPriceInput = document.getElementById('minPriceInput');
  const maxPriceInput = document.getElementById('maxPriceInput');
  const priceSlider = document.getElementById('priceRangeSlider');

  if (priceSlider && minPriceInput && maxPriceInput) {
    priceSlider.addEventListener('input', (e) => {
      const val = e.target.value;
      maxPriceInput.value = val;
    });
  }

  // 3. Clear Filters Handler
  const filterForm = document.getElementById('filterForm');
  const clearBtn = document.getElementById('clearFiltersBtn');

  if (clearBtn && filterForm) {
    clearBtn.addEventListener('click', () => {
      const searchBox = filterForm.querySelector('input[type="text"]');
      if (searchBox) searchBox.value = '';

      const checkboxes = filterForm.querySelectorAll('input[type="checkbox"]');
      checkboxes.forEach(cb => cb.checked = false);

      if (minPriceInput) minPriceInput.value = '0';
      if (maxPriceInput) maxPriceInput.value = '100';
      if (priceSlider) priceSlider.value = '100';

      const selectFields = filterForm.querySelectorAll('select');
      selectFields.forEach(select => select.selectedIndex = 0);

      filterForm.submit();
    });
  }

  // 4. Live Filtering Checkbox Autosubmit
  const autosubmitCheckboxes = document.querySelectorAll('.autosubmit-filter');
  autosubmitCheckboxes.forEach(cb => {
    cb.addEventListener('change', () => {
      filterForm.submit();
    });
  });
});
