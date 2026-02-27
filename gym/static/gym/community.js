document.addEventListener("DOMContentLoaded", function () {
  // no-op for now, but keeps file ready for future scoped init
});

/**
 * Build URL safely regardless of whether routes are under /gym/ or not.
 * COMMUNITY_ENDPOINTS is injected from template:
 * window.COMMUNITY_ENDPOINTS = { likeAdd: ".../like_add/", likeRemove: ".../like_remove/" }
 */
function getEndpointUrl(action, postId) {
  const endpoints = window.COMMUNITY_ENDPOINTS || null;

  const fallbackBase =
    action === "remove" ? "/like_remove/" : "/like_add/";

  const base =
    endpoints && (action === "remove" ? endpoints.likeRemove : endpoints.likeAdd)
      ? (action === "remove" ? endpoints.likeRemove : endpoints.likeAdd)
      : fallbackBase;

  const normalized = base.endsWith("/") ? base : base + "/";
  return `${normalized}${postId}/`;
}

function likeHandler(postId, initialLikedState) {
  let liked = initialLikedState;
  const url = getEndpointUrl(liked ? "remove" : "add", postId);

  fetch(url, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
    },
  })
    .then((response) => {
      if (!response.ok) {
        console.error("HTTP error:", response.status, response.statusText);
        return Promise.reject(new Error(response.statusText));
      }
      return response.json();
    })
    .then((data) => {
      const likeButton = document.getElementById(`like_button_${postId}`);
      const likeIcon = document.getElementById(`like_icon_${postId}`);
      const likeCount = document.getElementById(`like_count_${postId}`);

      if (!likeButton || !likeIcon || !likeCount) return;

      likeCount.textContent = data.like_count;
      liked = !liked;

      if (liked) {
        likeIcon.classList.remove("fa-regular");
        likeIcon.classList.add("fa-solid");
        likeButton.classList.add("liked");
      } else {
        likeIcon.classList.remove("fa-solid");
        likeIcon.classList.add("fa-regular");
        likeButton.classList.remove("liked");
      }

      likeButton.setAttribute("onclick", `likeHandler(${postId}, ${liked})`);
    })
    .catch((error) => {
      console.error("Error updating like:", error);
    });
}

/* =========================
   Custom modal logic
========================= */

function openEditModal(postId) {
  const modal = document.getElementById(`modal_edit_post_${postId}`);
  if (!modal) return;

  modal.classList.add("is-open");
  modal.setAttribute("aria-hidden", "false");
  document.body.style.overflow = "hidden";
}

function closeEditModal(postId) {
  const modal = document.getElementById(`modal_edit_post_${postId}`);
  if (!modal) return;

  modal.classList.remove("is-open");
  modal.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
}

function handleModalBackdrop(event, postId) {
  if (event.target.id === `modal_edit_post_${postId}`) {
    closeEditModal(postId);
  }
}

document.addEventListener("keydown", function (event) {
  if (event.key !== "Escape") return;

  const openModal = document.querySelector(".custom-modal.is-open");
  if (!openModal) return;

  openModal.classList.remove("is-open");
  openModal.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
});

/* =========================
   Edit post submit
========================= */

function handleSubmit(postId) {
  const contentEl = document.getElementById(`textarea_${postId}`);
  const imageUrlEl = document.getElementById(`image_url_${postId}`);

  if (!contentEl) return;

  const content = contentEl.value.trim();
  const image_url = imageUrlEl ? imageUrlEl.value.trim() : "";

  fetch(`/edit/${postId}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      content: content,
      image_url: image_url,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        return response.json().then((data) => Promise.reject(data));
      }
      return response.json();
    })
    .then((data) => {
      if (data.message) {
        const contentOut = document.getElementById(`content_${postId}`);
        if (contentOut) {
          contentOut.textContent = content;
        }

        // optional live image refresh
        const imageEl = document.getElementById(`post_image_${postId}`);
        if (imageEl && image_url) {
          imageEl.src = image_url;
          imageEl.style.display = "block";
        }

        closeEditModal(postId);
      } else if (data.error) {
        console.error("Error:", data.error);
        alert(data.error);
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      if (error && error.error) {
        alert(error.error);
      } else {
        alert("Something went wrong while updating the post.");
      }
    });
}

/* =========================
   Helpers
========================= */

function getCookie(name) {
  let cookieValue = null;

  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");

    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();

      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }

  return cookieValue;
}