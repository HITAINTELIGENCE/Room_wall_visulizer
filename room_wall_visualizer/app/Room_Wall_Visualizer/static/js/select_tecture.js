function selectTexture(image) {
    fetch(`/apply_texture/${image}`, {
        method: 'POST'
    }).then(response => response.json())
      .then(data => {
          if (data.state === 'success') {
              document.getElementById('imageResult').src = data.room_path;
          } else {
              alert('Error applying texture.');
          }
      }).catch(error => {
          console.error('Error:', error);
      });
}