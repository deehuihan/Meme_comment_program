function openTermsModal() {
    document.getElementById('termsModal').style.display = 'flex';
}

function closeTermsModal() {
    document.getElementById('termsModal').style.display = 'none';
}

function showPracticeModal(event) {
    event.preventDefault();
    document.getElementById('practiceModal').style.display = 'flex';
}

function closePracticeModal() {
    document.getElementById('practiceModal').style.display = 'none';
}

function submitForm() {
    document.getElementById('player-form').submit();
}

document.addEventListener('keyup', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        document.querySelector('.start-button').click();
    }
});