var visualize_flat = function (data_url, chart_selector) {

    var w = 900,
        h = 600,
        format = d3.format(",d");

    var pack = d3.layout.pack()
        .size([w - 4, h - 4])
        .value(function (d) {
            return d.size;
        });

    d3.select(chart_selector).select("svg").remove();
    var vis = d3.select(chart_selector).append("svg")
        .attr("width", w)
        .attr("height", h)
        .attr("class", "pack")
        .append("g")
        .attr("transform", "translate(2, 2)");

    d3.json(data_url, function (json) {
        var node = vis.data([json]).selectAll("g.node")
            .data(pack.nodes)
            .enter().append("g")
            .attr("class", function (d) {
                return d.children ? "node" : "leaf node";
            })
            .attr("transform", function (d) {
                return "translate(" + d.x + "," + d.y + ")";
            });

        node.append("title")
            .text(function (d) {
                return d.name;
            });

        node.append("circle")
            .transition().delay(100).duration(100)
            .attr("r", function (d) {
                return d.r;
            })
        ;

//        node.filter(
//            function (d) {
//                return !d.children;
//            }).append("text")
//            .attr("text-anchor", "middle")
//            .attr("dy", ".3em")
//            .text(function (d) {
//                return d.name.substring(0, d.r / 3);
//            });

        var leaves = node.filter(
            function (d) {
                return !d.children;
            });
        leaves.append("text")
              .attr("text-anchor", "middle")
              .attr("dy", "-5em");

        leaves.select("text").append("svg:tspan").attr('dy', '-1.2em').attr('x', 0).text(function(d) {return get_substring(d, 0)});
        leaves.select("text").append("svg:tspan").attr('dy', '1.2em').attr('x', 0).text(function(d) {return get_substring(d, 1)});
        leaves.select("text").append("svg:tspan").attr('dy', '1.2em').attr('x', 0).text(function(d) {return get_substring(d, 2)});
    });
};

function get_substring(d, i) {
    var lineLength = d.r / 3;
    return d.name.substring(lineLength*i, lineLength*(i+1));
}
//d3.json("http://localhost:8000/static/data/output_flat.json", function(json) {
//d3.json("http://localhost:8000/output_flat.json", visualize);

//function visualize_cluster(url) {
//    d3.json(url, visualize);
//}