/**
 * Smart Campus Lost & Found Matcher Frontend Scripts
 */

document.addEventListener('DOMContentLoaded', () => {
  // Mobile navigation hamburger toggle
  const navToggle = document.getElementById('navToggle');
  const navMenu = document.getElementById('navMenu');

  if (navToggle && navMenu) {
    navToggle.addEventListener('click', () => {
      navMenu.classList.toggle('show');
    });
  }

  // Auto-dismiss alerts after 5 seconds
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      setTimeout(() => alert.remove(), 400);
    }, 5000);
  });

  // Tab filtering on Items Catalog Page
  const tabButtons = document.querySelectorAll('.tab-btn');
  const lostSection = document.getElementById('lost-section');
  const foundSection = document.getElementById('found-section');

  if (tabButtons.length > 0 && lostSection && foundSection) {
    tabButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        tabButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const target = btn.getAttribute('data-target');
        if (target === 'all-sections') {
          lostSection.style.display = 'block';
          foundSection.style.display = 'block';
        } else if (target === 'lost-section') {
          lostSection.style.display = 'block';
          foundSection.style.display = 'none';
        } else if (target === 'found-section') {
          lostSection.style.display = 'none';
          foundSection.style.display = 'block';
        }
      });
    });
  }

  // Pre-fill today's date if date field is empty
  const dateInputs = document.querySelectorAll('input[type="date"]');
  dateInputs.forEach(input => {
    if (!input.value) {
      const today = new Date().toISOString().split('T')[0];
      input.value = today;
    }
  });

  // Confirmation on Marking as Returned
  const returnForms = document.querySelectorAll('form[action*="/status"]');
  returnForms.forEach(form => {
    form.addEventListener('submit', (e) => {
      const isReturned = form.querySelector('button').textContent.includes('Returned');
      if (isReturned) {
        if (!confirm('Are you sure you want to mark this item as Returned to its owner?')) {
          e.preventDefault();
        }
      }
    });
  });
});
