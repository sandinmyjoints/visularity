function show_scores(data_url, elm) {
    var dataset = [];
    d3.json(data_url, function (json) {
        dataset = json;

        d3.select(elm).select("table").remove();

        d3.select(elm)
            .append("table")
            .style("border-collapse", "collapse")
            .style("border", "2px black solid")
            .classed("centered similarity-scores", true)

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
//            .on("mouseover", function () {
//                d3.select(this).style("background-color", "aliceblue")
//            })
//            .on("mouseout", function () {
//                d3.select(this).style("background-color", "white")
//            })
            .style("background-color", function(d, i) {
                if (d==1 || d=="") {
                    return "gray";
                }
                if(isNaN(parseFloat(d))) {
                    return "#ededef";
                }

                return d > 0.2 ? "lightgreen": "pink"
            })
            .text(function (d) {
                return d;
            })
            .style("font-size", "12px");
    })
}
