    function getColor(d){
             return     d < 11? "#9CFF9C":
                        d < 23? "#31FF00":
                        d < 35? "#31CF00":
                        d < 41? "#FFFF00":
                        d < 47? "#FFCF00":
                        d < 53? "#FF9A00":
                        d < 58? "#FF6464":
                        d < 64? "#FF0000":
                        d < 70? "#990000":
                                "#CE30FF";
        /*
             return     d < 15.4? "#31CF00":
                        d < 35.4? "#FFFF00":
                        d < 54.4? "#FF9A00":
                        d < 150.4? "#FF0000":
                        d < 250.4? "#CE00CE":
                        d < 350.4? "#990000":
                        d < 500.4? "#990000":
                                "#990000";
        */

    }

    var legend = L.control({position: 'bottomright'});

    legend.onAdd = function (map) {
    
        var div = L.DomUtil.create('div', 'info legend'),
        labels = [],
        grades = [0,11,23,35,41,47,53,58,64,70];
        // grades = [0,15.4,35.4,54.4,150.4,250.4,350.4,500.4];

        // loop through our density intervals and generate a label with a colored square for each interval
        for (var i = 0; i < grades.length; i++) {
            div.innerHTML += labels.push(
                '<i style="background:' + getColor(grades[i]+1) + ';">&nbsp;&nbsp;&nbsp;&nbsp;</i> ' +
                grades[i] + (grades[i + 1] ? '&ndash;' + grades[i + 1] : '+'));
        }
        div.innerHTML = "<table border=1 bgcolor=\"#ffffff\" cellspacing=0 cellpadding=5><tr><td bgcolor=\"#ffffff\">" + labels.join('<br>') + "</td></tr></table>";
    
        return div;
    };

    legend.addTo(map);

