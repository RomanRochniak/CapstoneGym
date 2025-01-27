document.addEventListener("DOMContentLoaded", () => {

    const elements = document.querySelectorAll(".fade-in, .slide-in-left");

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("visible");
                }
            });
        },
        { threshold: 0.1 }
    );

    elements.forEach((el) => observer.observe(el));

});

document.addEventListener("DOMContentLoaded", () => {
    const fogElements = document.querySelectorAll(".fade-in-fog");

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("visible");
                }
            });
        },
        { threshold: 0.5 }
    );

    fogElements.forEach((el) => observer.observe(el));
});

document.addEventListener("DOMContentLoaded", () => {
    const priceCards = document.querySelectorAll(".price__card");

    priceCards.forEach(card => {
        card.classList.add("price__card-hover");
    });
});
document.addEventListener("DOMContentLoaded", () => {
    const joinCards = document.querySelectorAll(".join__grid");

    joinCards.forEach(card => {
        card.classList.add("join__grid-hover");
    });
});
document.addEventListener("DOMContentLoaded", () => {
    const priceCards = document.querySelectorAll(".explore__card");

    priceCards.forEach(card => {
        card.classList.add("explore__card-hover");
    });
});

document.addEventListener("DOMContentLoaded", () => {
    const contentElement = document.querySelector(".class__content");
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("fade-in-content");
                }
            });
        },
        { threshold: 0.5 }
    );

    if (contentElement) {
        observer.observe(contentElement);
    }
});

