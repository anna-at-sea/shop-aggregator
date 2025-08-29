document.addEventListener('DOMContentLoaded', function () {
    const productList = document.getElementById("product-list");
    const loadMoreBtn = document.getElementById("load-more-btn");

    if (loadMoreBtn) {
        loadMoreBtn.addEventListener("click", function () {
            const nextPage = this.dataset.nextPage;
            fetch(`?page=${nextPage}`, { headers: { "X-Requested-With": "XMLHttpRequest" } })
                .then(response => response.json())
                .then(data => {
                    productList.insertAdjacentHTML("beforeend", data.html);
                    if (data.has_next) {
                        this.dataset.nextPage = data.next_page;
                    } else {
                        this.remove();
                    }
                    attachLikeEvents();
                });
        });
    }

    function attachLikeEvents() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        document.querySelectorAll('.like-btn').forEach(btn => {
            if (!btn.dataset.bound) {
                btn.dataset.bound = "true";
                btn.addEventListener('click', function () {
                    const productId = this.dataset.productId;
                    const url = toggleLikeUrl.replace('0', productId);  // 👈 more on this below

                    fetch(url, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken,
                            'Content-Type': 'application/json'
                        },
                    })
                    .then(response => response.json())
                    .then(data => {
                        this.textContent = data.status === 'liked' ? '❤️' : '🤍';
                    })
                    .catch(error => console.error('Error:', error));
                });
            }
        });
    }

    attachLikeEvents();
});
