// script.js
// kakao.maps.load(() => {
//     initMap();
// });

// function resizeMap() {
//     const mapElement = document.getElementById("map");
//     mapElement.style.width = `${window.innerWidth}px`;
//     mapElement.style.height = `${window.innerHeight}px`;
// }
let map;
let markers;
let ps;
let infowindow;
let activeOverlay;

function initMap(lat=37.555946,lng=126.972317) {
    const mapContainer = document.getElementById('map'), // 지도를 표시할 div 
    mapOption = {
        center: new kakao.maps.LatLng(lat, lng), // 지도의 중심좌표
        level: 5 // 지도의 확대 레벨
    };  
    // 지도를 생성합니다    
    map = new kakao.maps.Map(mapContainer, mapOption); 
    // 장소 검색 객체를 생성합니다
    ps = new kakao.maps.services.Places();  
    // 검색 결과 목록이나 마커를 클릭했을 때 장소명을 표출할 인포윈도우를 생성합니다
    infowindow = new kakao.maps.InfoWindow({zIndex:1});
    markers = [];
    activeOverlay = null; // 현재 열려있는 오버레이를 추적

    window.addEventListener('resize', function() {
        const mapElement = document.getElementById("map");
        mapElement.style.width = `${window.innerWidth}px`;
        mapElement.style.height = `${window.innerHeight}px`;
        map.relayout();
    });
    // setMapFunctions(map, ps, infowindow, markers);
    return undefined;
}

// >>>>>>>>> Search Engine >>>>>>>>>
// 키워드 검색을 요청하는 함수입니다
function searchPlaces() {
    var keyword = document.getElementById('keyword').value;
    // console.log(`
    // map: ${map},
    // ps: ${ps},
    // markers: ${markers},
    // `)
    console.log(`search keyword ${keyword}`)
    if (!keyword.replace(/^\s+|\s+$/g, '')) {
        alert('키워드를 입력해주세요!');
        return false;
    }

    // console.log(`requrest keywordSearch`)
    // 장소검색 객체를 통해 키워드로 장소검색을 요청합니다
    ps.keywordSearch(keyword, placesSearchCB); 
}
// 장소검색이 완료됐을 때 호출되는 콜백함수 입니다
function placesSearchCB(data, status, pagination) {
    if (status === kakao.maps.services.Status.OK) {
        // console.log("✅ ", status)
        // 정상적으로 검색이 완료됐으면
        // 검색 목록과 마커를 표출합니다
        displayPlaces(data);

        // 페이지 번호를 표출합니다
        displayPagination(pagination);

    } else if (status === kakao.maps.services.Status.ZERO_RESULT) {

        alert('검색 결과가 존재하지 않습니다.');
        return;

    } else if (status === kakao.maps.services.Status.ERROR) {

        alert('검색 결과 중 오류가 발생했습니다.');
        return;

    }
}
// 검색 결과 목록을 표출하는 함수입니다
function displayPlaces(places) {
    // console.log("✅ start displayPlaces")
    var listEl = document.getElementById('placesList'), 
    menuEl = document.getElementById('menu_wrap'),
    fragment = document.createDocumentFragment(), 
    bounds = new kakao.maps.LatLngBounds(), 
    listStr = '';
    
    // 검색 결과 목록에 추가된 항목들을 제거합니다
    removeAllChildNods(listEl);
    // 지도에 추가된 마커들을 제거합니다.
    hideMarkers();

    // 지도에 표시되고 있는 마커를 제거합니다
    // removeMarker();
    
    for ( var i=0; i<places.length; i++ ) {
        // console.log("✅ places length:", places.length)
        // 마커를 생성하고 지도에 표시합니다
        var placePosition = new kakao.maps.LatLng(places[i].y, places[i].x),
            // marker = addMarker(placePosition, i), 
            itemEl = getListItem(i, places[i]); // 검색 결과 항목 Element를 생성합니다

        // 검색된 장소 위치를 기준으로 지도 범위를 재설정하기위해
        // LatLngBounds 객체에 좌표를 추가합니다
        // bounds.extend(placePosition);
        if (i === 0) { // 첫 번째 검색 결과의 위치로 지도 범위를 재설정하기 위함.
            bounds.extend(placePosition);
        }
        fragment.appendChild(itemEl); // item 요소들을 DocumentFragment에 우선 추가하고 나주에 한번에 웹 페이지에 추가.
    }

    // 검색결과 항목들을 검색결과 목록 Element에 추가합니다
    listEl.appendChild(fragment);
    menuEl.scrollTop = 0;

    // 검색된 장소 위치를 기준으로 지도 범위를 재설정합니다
    // map.setBounds(bounds);
}
// 검색결과 항목을 Element로 반환하는 함수입니다
function getListItem(index, places) {
    // console.log("✅ start getListItem")
    // places.y = latitude
    // places.x = longitude
    // console.log(`places.place_name = ${places.place_name}
// places.road_address_name = ${places.road_address_name}
// `)
    var el = document.createElement('li');
    el.className = 'item';
    // ▶ marker span 생성
    const markerSpan = document.createElement('span');
    markerSpan.className = `markerbg marker_${index + 1}`;
    // ▶ info div 생성
    const infoDiv = document.createElement('div');
    infoDiv.className = 'info';
    infoDiv.dataset.lat = places.y;
    infoDiv.dataset.lng = places.x;
    infoDiv.dataset.roadname = places.road_address_name;
    infoDiv.dataset.name = places.place_name ? places.place_name : ''
    infoDiv.innerHTML = `
        <h5>${places.place_name}</h5>
        <span>${places.road_address_name || places.address_name}</span>
        ${places.road_address_name ? `<span class="jibun gray">${places.address_name}</span>` : ''}
        <span class="tel">${places.phone}</span>
    `;
    // ▶ 클릭 이벤트 연결
    infoDiv.onclick = function () {
        const lat = parseFloat(infoDiv.dataset.lat);
        const lng = parseFloat(infoDiv.dataset.lng);
        const roadname = infoDiv.dataset.roadname;
        const name = infoDiv.dataset.name;
        panToNDrawMarker(lat, lng, roadname, name);
    };

    // ▶ el에 span과 div 모두 추가
    el.appendChild(markerSpan);
    el.appendChild(infoDiv);
    return el;
};
// 검색결과 목록 하단에 페이지번호를 표시는 함수입니다
function displayPagination(pagination) {
    // console.log("✅ start displayPagination")
    var paginationEl = document.getElementById('pagination'),
        fragment = document.createDocumentFragment(),
        i; 

    // 기존에 추가된 페이지번호를 삭제합니다
    while (paginationEl.hasChildNodes()) {
        paginationEl.removeChild (paginationEl.lastChild);
    }

    for (i=1; i<=pagination.last; i++) {
        var el = document.createElement('a');
        el.href = "#";
        el.innerHTML = i;

        if (i===pagination.current) {
            el.className = 'on';
        } else {
            el.onclick = (function(i) {
                return function() {
                    pagination.gotoPage(i);
                }
            })(i);
        }

        fragment.appendChild(el);
    }
    paginationEl.appendChild(fragment);
}

// 검색결과 목록 또는 마커를 클릭했을 때 호출되는 함수입니다
// 인포윈도우에 장소명을 표시합니다
// function displayInfowindow(marker, title) {
//     var content = '<div style="padding:5px;z-index:1;">' + title + '</div>';

//     infowindow.setContent(content);
//     // infowindow.open(map, marker);
// }
// 검색결과 목록의 자식 Element를 제거하는 함수입니다
function removeAllChildNods(el) {   
    // console.log("✅ start displayPlaces")
    while (el.hasChildNodes()) {
        el.removeChild (el.lastChild);
    }
}
// <<<<<<<<< Search Engine <<<<<<<<<


// >>>>>>>>> Marker >>>>>>>>>
function panToNDrawMarker(lat, lng, roadname, name) {
    console.log("✅ start panToNDrawMarker")
    console.log(`lat,lng=(${lat},${lng})
roadname=${roadname}
`)
    // - y,x = lat, lng
    // - road_address_name = 도로명주소
    // 이동할 위도 경도 위치를 생성합니다 
    var moveLatLon = new kakao.maps.LatLng(lat, lng);
    // 지도 중심을 부드럽게 이동시킵니다
    // 만약 이동할 거리가 지도 화면보다 크면 부드러운 효과 없이 이동합니다
    map.panTo(moveLatLon); 

    drawMarker(lat, lng, roadname, name);
};

function drawMarker(lat,lng,roadname, name) {
    console.log("✅ start drawMarkers")
    // 마커가 표시될 위치입니다 
    var markerPosition  = new kakao.maps.LatLng(lat, lng); 

    // 마커를 생성합니다
    addMarker(markerPosition, roadname, name);
}

// 마커를 생성하고 지도위에 표시하는 함수입니다
function addMarker(position, roadname, name) {
    console.log("✅ start addMarkers")
    // 마커를 생성합니다
    var marker = new kakao.maps.Marker({
        position: position,
        clickable: true // 마커를 클릭했을 때 지도의 클릭 이벤트가 발생하지 않도록 설정합니다 >> 지도의 클릭 이벤트가 marker에 발생한다.
    });

    // 1. 마커가 클릭되면 서버에 예측함수를 호출합니다.
    // 2. 서버에서 받은 이미지를 CustomOverlay의 컨텐츠로 추가합니다.
    // 3. 닫기가 가능한 CustomOverlay를 마커에 추가합니다.
    kakao.maps.event.addListener(marker, 'click', async function() {
        // 1. 서버에 예측 이미지 요청 (예: /predict?lat=xxx&lng=xxx)
        let lat = position.getLat();
        let lng = position.getLng();

        let response = await fetch(`/inference?lat=${lat}&lng=${lng}`);
        let data = await response.json(); // 서버는 { image_url: "..." } 형태로 응답
        const content = `
            <div class="wrap">
                <div class="info">
                    <div class="title">
                        🔎3개월 실거래가 예측
                        <div class="close" onclick="closeOverlay()" title="닫기"></div>
                    </div>
                    <div class="body">
                        <div class="img">
                            <img src="${data.image_url}">
                        </div>
                        <div class="desc">
                            <div class="ellipsis">${name === "" ? roadname : name + ' (' + roadname + ')'}</div>
                            <div>(lat: ${lat.toFixed(5)}, lng: ${lng.toFixed(5)})</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 기존 오버레이가 있다면 닫음
        if (activeOverlay) {
            activeOverlay.setMap(null);
        }
        // 새 오버레이 생성
        const overlay = new kakao.maps.CustomOverlay({
            content: content,
            position: position,
            map: map
        });
        // 오버레이를 추적 변수에 저장
        activeOverlay = overlay;

        // 닫기 함수도 오버레이에 연결
        window.closeOverlay = function () {
            overlay.setMap(null);
            activeOverlay = null;
        };

        // 오버레이의 중앙으로 맵 이동
        let projection = map.getProjection();
        let loc2point = projection.pointFromCoords(new kakao.maps.LatLng(lat, lng))
        let movedPoint = new kakao.maps.Point(loc2point.x + 250, loc2point.y - 280)
        let movedLoc = projection.coordsFromPoint(movedPoint);
        map.panTo(movedLoc);

    });

    // 마커가 지도 위에 표시되도록 설정합니다
    marker.setMap(map);
    
    // 생성된 마커를 배열에 추가합니다
    markers.push(marker);
}
// 배열에 추가된 마커들을 지도에 표시하거나 삭제하는 함수입니다
function setMarkers(map) {
    console.log("✅ start setMarkers")
    for (var i = 0; i < markers.length; i++) {
        markers[i].setMap(map);
    }            
}
// "마커 감추기" 버튼을 클릭하면 호출되어 배열에 추가된 마커를 지도에서 삭제하는 함수입니다
function hideMarkers() {
    console.log("✅ start hideMarkers")
    setMarkers(null);    
}
// <<<<<<<<< Marker <<<<<<<<< 