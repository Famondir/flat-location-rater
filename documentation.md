# Flat location rater

This should help to rate flats regarding the travel time one would face based on ones regular schedule.

## Working process

### December

#### 22-12-24

* tried to crawl information from immoscout24 - failed (at least) because of well working bot protection
  * alternatively to crawling locations of flats one could provide the locations manually
  * maybe by passing the source code of the site that is rendered after the manual search?
  * can the dots on the map in hybrid mode help?
* playing around with Jannis' bvg API
* having a look at [fredy](https://github.com/orangecoding/fredy) app to find flats
  * utilizing up to date flat web crawler to get flet locations
  * saving as a list / csv and use in own program

#### 23-12-24

* set up falsk and react project

#### 25-12-24

* tried different routing api's (mapbox, osrm) for walking, cycling and driving
* set up dashboard framework
* explored address grainity 
  * intersecting Kiez name and PLZ if both given and street name is missing
* walking speed: 80 m per min
  * h3 hexes on resolution 10 have max 73 m radius
  * each additional detail grade multiplies api calls by 6.5
  * for resolution 10 there would be 890 hexes for **Rudow**; maybe stop at resoltution 9 for standard

#### 26-12-24

* asynch url requests to reduce calculation time
* added leaflet map to app
  * showing markers with different color
  * showing regions as polygons

#### 28-12-24

* getting coordinagtes and geojson from Nominatim
* passing correct geojson
* regions can have fill opacity now given via properties

#### 29-12-24

* trying to gret better street shapes; nominatim does not return complete onres

#### 30-12-24

* getting better street shapes from local dataset

#### 1-1-25

* storing data in database for preventing requesting same urls multiple times

#### 2-1-25

* adding overview table about traveltimes

#### 3-1-25

* fixing problem with nan values for travel time data transmission
* linked table and map for hover and click
* added modal to show details for single flats (with hex polygons)
* added project description with images