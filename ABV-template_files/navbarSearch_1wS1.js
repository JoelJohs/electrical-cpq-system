// Archivo: `static/publico/js/nav/navbarSearch.js`
document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('navbar-search');
  const resultsContainer = document.getElementById('navbar-search-results');
  let timeout = null;

  searchInput.addEventListener('input', () => {
    clearTimeout(timeout);
    const query = searchInput.value.trim();
    if (query.length === 0) {
      resultsContainer.innerHTML = '';
      resultsContainer.classList.remove('show');
      return;
    }
    timeout = setTimeout(() => {
      const params = new URLSearchParams({ q: query });
      fetch(`/search/?${params}`, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(response => response.json())
        .then(data => {
          resultsContainer.innerHTML = data.results_html;
          if (data.results_html.trim()) {
            resultsContainer.classList.add('show');
          } else {
            resultsContainer.classList.remove('show');
          }
        });
    }, 300);
  });

  // Maneja redirección al presionar Enter en el input de búsqueda
  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      window.location.href = `/products/?search=${encodeURIComponent(searchInput.value)}`;
    }
  });

  document.addEventListener('click', (e) => {
    if (!resultsContainer.contains(e.target) && e.target !== searchInput) {
      resultsContainer.classList.remove('show');
    }
  });
});