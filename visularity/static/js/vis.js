function show_scores(data_url, elm) {
    var dataset = [];
    d3.json(data_url, function (json) {
        dataset = json;
        min_score = d3.min(dataset, function(arr) {
            return d3.min(arr, function(d) {
                if(isNaN(parseFloat(d))) {
                    return 0;
                }
                return d == 1 ? 0 : d; // ignore 1s
            });
        });
        max_score = d3.max(dataset, function(arr) {
            return d3.max(arr, function(d) {
                if(isNaN(parseFloat(d))) {
                    return 0;
                }
                return d == 1 ? 0 : d; // ignore 1s
            });
        });
        var scale = d3.scale.linear().domain([min_score, max_score]).nice().range([0, 1]);
        var color = d3.interpolateRgb("#eee", "#5A8");

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
                    return "white";
                }

//                return d > 0.2 ? "lightgreen": "white"
                return color(scale(d));
            })
            .text(function (d) {
                return d;
            })
            .style("font-size", "12px");
    })
}
