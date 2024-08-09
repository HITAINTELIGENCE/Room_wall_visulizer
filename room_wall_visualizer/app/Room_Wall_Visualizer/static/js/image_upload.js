// Function to read and display the selected image
function readURL(input) {
    // Check if there are any files selected
    if (input.files && input.files[0]) {
        var reader = new FileReader(); // Create a new FileReader object

        // Define what happens when the file is read successfully
        reader.onload = function (e) {
            // Set the src attribute of the imageResult element to the file's data URL
            $('#imageResult').attr('src', e.target.result);
        };
        // Read the selected file as a data URL
        reader.readAsDataURL(input.files[0]);
    }
}

// jQuery function to handle the file input change event
$(function () {
    // Add an event listener to the file input element
    $('#upload').on('change', function () {
        readURL(input); // Call readURL function with the current input element
    });
})

// Get references to the file input and the label element
var input = document.getElementById('upload');
var infoArea = document.getElementById('upload-label');

// Add an event listener to display the selected file name
input.addEventListener('change', showFileName);


// Function to display the selected file name
function showFileName(event) {
    var input = event.srcElement; // Get the input element that triggered the event
    var fileName = input.files[0].name; // Get the name of the selected file
    // Update the text content of the infoArea element with the file name
    infoArea.textContent = 'File name: ' + fileName;
}

// jQuery function to handle the form submission event
$(function () {
    // Add an event listener to the form element
    $('#uploadForm').on('submit', function (event) {
        // Show the loading message when the form is submitted
        $('#loadingMessage').show();
    });
});


function handleImageUpload(event) {
    const file = event.target.files[0];
    if (file) {
      // Preview the image
      const reader = new FileReader();
      reader.onload = function(e) {
        document.getElementById('imageResult').src = e.target.result;
      }
      reader.readAsDataURL(file);
  
      // Send the image to the server for processing
      const formData = new FormData();
      formData.append('file', file);
      formData.append('button', 'texture'); // or 'color', depending on what you want to do by default
  
      fetch("/room_visualization_prediction", {
        method: 'POST',
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        // Handle the response from the server
        console.log(data);
        // You might want to update the UI here based on the response
      })
      .catch(error => {
        console.error('Error:', error);
      });
    }
  }