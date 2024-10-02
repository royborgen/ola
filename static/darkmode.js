// check for saved 'darkMode' in localStorage
let darkMode = localStorage.getItem('darkMode'); 

const darkModeToggle = document.querySelector('#dark-mode-toggle');
const lightIcon = document.getElementById("light-icon");
const darkIcon = document.getElementById("dark-icon");

const enableDarkMode = () => {
  // Add the class to the body
  document.body.classList.add('darkmode');
  // Update darkMode in localStorage
  localStorage.setItem('darkMode', 'enabled');
  lightIcon.style.display = "block";
  darkIcon.style.display = "none";
}

const disableDarkMode = () => {
  // Remove the class from the body
  document.body.classList.remove('darkmode');
  // Update darkMode in localStorage
  localStorage.setItem('darkMode', 'disabled');
  lightIcon.style.display = "none";
  darkIcon.style.display = "block";
}

// Check for darkMode preference on page load and set icon visibility
if (darkMode === 'enabled') {
  enableDarkMode();
} else {
  disableDarkMode();
}

// Toggle dark mode when button is clicked
darkModeToggle.addEventListener('click', () => {
  darkMode = localStorage.getItem('darkMode'); 
  
  if (darkMode !== 'enabled') {
    enableDarkMode();
  } else {  
    disableDarkMode(); 
  }
});
