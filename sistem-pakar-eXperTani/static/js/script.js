document.addEventListener('DOMContentLoaded', function() {
    var infoIcon = document.querySelector('.info-icon');
    var hoverMessage = document.querySelector('.hover-message');

    infoIcon.addEventListener('mouseover', function() {
        hoverMessage.style.display = 'block';
    });

    infoIcon.addEventListener('mouseout', function() {
        hoverMessage.style.display = 'none';
    });
});


  document.querySelectorAll('.btn-link').forEach(function(button) {
    button.addEventListener('click', function(event) {
      const targetId = button.getAttribute('data-target');
      const targetElement = document.querySelector(targetId);

      // Check if the target element is currently shown
      const isShown = targetElement.classList.contains('show');

      // If the target element is shown, prevent the default collapse behavior
      if (isShown) {
        event.preventDefault();
        event.stopPropagation();

        // Manually toggle the collapse state
        $(targetId).collapse('hide');
      }
    });
  });


