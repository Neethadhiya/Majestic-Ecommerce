const formControl = document.querySelector('.form-control');
const label = document.querySelector('label[for="exampleInput"]');

formControl.addEventListener('focus', () => {
  label.classList.add('active');
});

formControl.addEventListener('blur', () => {
  if (formControl.value === '') {
    label.classList.remove('active');
  }
});
