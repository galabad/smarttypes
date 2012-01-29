
var global_group_idx = 0;

var start_page = function(num_groups){

    var coord_scale = d3.scale.linear().domain([0,1]).range([10,400]);
    var color_scale = d3.scale.linear().domain([0,num_groups])
        .interpolate(d3.interpolateRgb)
        .range(["#cccccc", "#000000"]);
    
    var svg = d3.select("#map_data").append("svg")
        .attr("width", 475)
        .attr("height", 425);
        
    d3.json('/social_map/map_data.json', function(data){
        //console.log(data);
        svg.selectAll("circle")
            .data(data)
            .enter().append("circle")
            .attr("class", function(d, i) { return "group_" + d.group_index; })
            .attr("cx", function(d, i) { return coord_scale(d.x); })
            .attr("cy", function(d, i) { return coord_scale(d.y); })
            .attr("r", 3)
            .style("fill", function(d, i) { return color_scale(d.group_index); })
            .style("cursor", "pointer")
            .on("click", function(d,i) { show_cluster(d.group_index); });
            
        show_cluster(global_group_idx);
    });
      
    $('a#decrement_group').click(function(e){
        if (global_group_idx == 0){
            global_group_idx = (num_groups - 1);
        }
        else{
            global_group_idx -= 1;
        }
        show_cluster(global_group_idx);
    });      
    
    $('a#increment_group').click(function(e){
        if (global_group_idx == (num_groups - 1)){
            global_group_idx = 0;
        }
        else{
            global_group_idx += 1;
        }
        show_cluster(global_group_idx);
    });
}

var old_group_index = -1;
var old_group_color = "";
var show_cluster = function(group_idx){
    //change the old color back
    if (old_group_index != -1){
        d3.selectAll('circle.group_' + old_group_index).style("fill", old_group_color);
    }
    global_group_idx = group_idx;
    old_group_index = group_idx;
    old_group_color = d3.selectAll('circle.group_' + group_idx).style("fill");
    d3.selectAll('circle.group_' + group_idx).style("fill", '#00FF00');
    $('#current_group').html(group_idx + 1);
    $.ajax({type:"POST",
            url:"/social_map/ajax_group",
            cache:false,
            data:{'group_index': group_idx},
            dataType:"html",
            error:function(){},
            success:function(html){
                $('#group_details').html('');
                $('#group_details').html(html);
                d3.selectAll("li.twitter_user").style("background-color", function(d, i) { return i % 2 ? "#fff" : "#eee"; });
            }
    });
};





