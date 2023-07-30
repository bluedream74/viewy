'use strict'


$(document).ready(function () {
    let debounce;
    const DEBOUNCE_DELAY = 500;

    $('#search').off('input').on('input', function (e) {
        clearTimeout(debounce);

        debounce = setTimeout(() => {
            $.ajax({
                type: "GET",
                url: '/posts/auto_correct/',
                data: {
                    'search_text': $('#search').val()
                },
                success: function (data) {
                    $('#search-results').empty();
                    for (let item of data) {
                        if (item.type === 'hashtag') {
                            let listItem = $('<li><i class="fas fa-hashtag"></i> ' + item.value + '</li>');
                            listItem.click(function () {
                                $('#search').val(item.value);  // Set the search bar's value to the clicked item's value
                                $('.search-bar').submit();  // Automatically submit the form when an item is clicked
                            });
                            $('#search-results').append(listItem);
                        }
                    }
                },
                error: function (error) {
                    console.error("Error fetching search suggestions:", error.status, error.statusText);
                }
            });
        }, DEBOUNCE_DELAY);
    });
});