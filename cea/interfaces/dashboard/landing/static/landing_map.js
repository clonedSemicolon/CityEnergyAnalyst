var map;
var latlngs = [];
var temp = [];
var polygon = L.polygon(latlngs, {color: 'red'});
// var temppoly = L.polygon(temp, {color: 'red'});
var lat = $("#latitude").val();
var lon = $("#longitude").val();

// const lassoResult = document.querySelector("#lassoResult");

map = L.map('mapid').setView([lat, lon], 11);

L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png',
    {attribution: "Data copyright OpenStreetMap contributors"}).addTo(map);

map.on('click', onMapClick);

	// Not sure whether to add hover functionality
	// map.on('mousemove', onMapHover);

function goToLocation() {
	var lat = $("#latitude").val();
	var lon = $("#longitude").val();
	map.setView([lat, lon], 11);
}

function onMapClick(e) {
    latlngs.push(e.latlng)
	map.removeLayer(polygon)
	polygon = L.polygon(latlngs, {color: 'red'})
	polygon.addTo(map);

	// if (typeof latlngs !== 'undefined') {
  	// 	lassoResult.innerHTML = latlngs.toString();
	// }
}

function onMapHover(e) {
	if (latlngs.length !== 0) {
		map.removeLayer(temppoly)
		temp = [...latlngs]
		temp.push(e.latlng)
		temppoly = L.polygon(temp, {color: 'red'})
		temppoly.addTo(map);
	}
}

function removePoly() {
	// lassoResult.innerHTML = "";
	latlngs = [];
	map.removeLayer(polygon);
	$("#polyString").val("");
	// temp = [];
	// map.removeLayer(temppoly);
}

function polyToString() {
	if ($('#zone').prop('checked') && latlngs.length < 3) {
		alert("Please select a site with a polygon")
	} else {
		// TODO: Check if polygon is empty
		var json = polygon.toGeoJSON();
		L.extend(json.properties, polygon.properties);
		$("#poly-string").val(JSON.stringify(json));
	}
}

$(document)
