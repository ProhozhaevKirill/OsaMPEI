let timeLeft = 600;
function updateTimer() {
    let minutes = Math.floor(timeLeft / 60);
    let seconds = timeLeft % 60;
    document.getElementById('timer').innerText = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
    if (timeLeft > 0) {
        timeLeft--;
        setTimeout(updateTimer, 1000);
    }
}
updateTimer();
