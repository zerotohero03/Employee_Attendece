// Add any custom JavaScript here

// Example: Profile picture preview
function previewProfilePicture(event) {
    const reader = new FileReader();
    reader.onload = function() {
      const output = document.getElementById('profile-picture-preview');
      output.src = reader.result;
    };
    reader.readAsDataURL(event.target.files[0]);
  }
  