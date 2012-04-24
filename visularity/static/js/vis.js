function show_scores(data_url, elm) {
    var dataset = [];
    d3.json(data_url, function (json) {
        dataset = json;

        d3.select(elm).select("table").remove();

        d3.select(elm)
            .append("table")
            .style("border-collapse", "collapse")
            .style("border", "2px black solid")

            .selectAll("tr")
            .data(dataset)
            .enter().append("tr")

            .selectAll("td")
            .data(function (d) {
                return d;
            })
            .enter().append("td")
            .style("border", "1px black solid")
            .style("padding", "10px")
            .on("mouseover", function () {
                d3.select(this).style("background-color", "aliceblue")
            })
            .on("mouseout", function () {
                d3.select(this).style("background-color", "white")
            })
            .text(function (d) {
                return d;
            })
            .style("font-size", "12px");
    })
}
