const box1 = document.getElementById("container1");
const box2 = document.getElementById("container2");
const box3 = document.getElementById("container3");

// Lägg in dessa i en array i önskad "startordning"
let containers = [box1, box2, box3];

/**
 * Sätter klasser för position (x/y) och z-index baserat på
 * array-ordningen: [0] = front, [1] = middle, [2] = back.
 */
function setPositionsAndZIndex() {
  // Ta först bort alla position-/z-klasser på samtliga
  containers.forEach((el) => {
    el.classList.remove(
      "front", "middle", "back",
      "frontPos", "middlePos", "backPos"
    );
  });

  // Sätt "front" + "frontPos" på index 0
  containers[0].classList.add("front", "frontPos");

  // Sätt "middle" + "middlePos" på index 1
  containers[1].classList.add("middle", "middlePos");

  // Sätt "back" + "backPos" på index 2
  containers[2].classList.add("back", "backPos");
}
/**
 * När man klickar på en container ska den flyttas till
 * första platsen i arrayen (dvs bli "front").
 */
function bringToFront(clickedEl) {
  // Hitta index för det klickade elementet
  const i = containers.indexOf(clickedEl);
  if (i > -1) {
    // Ta ur den från sin nuvarande position ...
    // ... och lägg den i början (unshift)
    containers.unshift(...containers.splice(i, 1));
  }
  // Uppdatera klasser
  setPositionsAndZIndex();
}

// Sätt klick-lyssnare på alla containrar
containers.forEach(el => {
  el.addEventListener("click", () => {
    bringToFront(el);
  });
});