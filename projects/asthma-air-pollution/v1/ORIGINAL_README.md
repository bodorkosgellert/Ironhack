# Asthma and Air Pollution

* [Asthma](#asthma)
* [Datasets](#datasets)
* [Statistical methods](#statistical-methods)
* [Conclusions](#conclusions)
* [Links](#links)



## Asthma
Asthma is a chronic lung disease that is caused by inflammation and an overreaction of the immune system. Symptoms can be episodes of wheezing, coughing, chest tightness, and shortness of breath. One of the environmental triggers is the quality of inhaled air, which is influenced by many factors, one of them is the relative concentration of air pollutants. In this project I was looking at air pollution levels and attempting to see if it can be linked to the relative incidence of astma in different geographical regions


## Datasets
The prevalance of asthma in the adult population is on a global average approximately 1 adult in every 13, however the statistical distribution shows a great variance. I have used the 'PLACES: Local Data for Better Health ' dataset to get the diagnosed asthma ratio percentages and geographically based statistics for the machine learning algorithms. The air pollution datasets were from different websites as I couldn’t find a single one that would have satisfactory quality of all the substance levels I wanted to calculate. I have used one selected state in the United States for each calculations. The first dataset was to see if there’s an easy way to train a model that could predict the incidence of asthma from the measured PM2.5 values in the same geographic region. The second one was focusing on PM10 values, and the third one on gases and substances negatively associated with particular matter presence in the atmosphere. Based on observations and individual reports, the asthma symptoms were triggered by bad air quality, in particular by particle pollution 


## Statistical methods
I used linear regression, KNN, and random forests to see the predictive value of the datasets. The first dataset had a yearly documented number of 1175 census tracts, the second 1516, the third one 791 and I have assigned the matching locally recorded air pollutant values for the statistical measures. The machine learning calculations would arguably have better results with a higher data amount. The publicly available datasets were documented for informative and forecasting purposes and not scientific calculations, which influences the results of the calculations. Understanding the problem and the trends detailed in this project, and the planning of more accurate calcluations does depend on the datasets available

## Conclusions
The results seemed to show a very weak link between the first two studied cases that in itself didn't prove to be a determining factor. The air quality is just one of the many factors that influence asthma severity, and the datasets lacked the accuracy to identify the effect of air pollutants on a consistent basis. They can however be used to provide a good methodological framework for refined analysis. The third calculation showed very high negative R2 scores which means the model showed to have a low predictive value on the likelihood of having asthma. One way to interpret the ineffectiveness of the model is that ozone levels show a negative link with particle pollution concentration. 

As the effect of influencing factors tend to be consistent across all populations, the aspects of urban planning and individual life choices are also worth considering here. Most of the symptom free population can not intuitively feel the air pollution levels unless the extremely bad cases, and the higher sensitivity of people living with asthma makes data based calculations a relevant topic. A good understanding of air pollutant interactions over the span of decades, the air quality indicators, and the influecing factors contributing to air impurity knowing the effects of genetic predisposition can lead to improved lifestyle choices. Understanding and predicting the weight of air pollutants can make a difference in evaluating decisions on the daily life of those effected directly or indirectly by asthma 

## Links
* https://www.cdc.gov/places/index.html
* https://data.world/data-society/us-air-pollution-data
* https://aqicn.org/city/usa/alabama
* https://www.epa.gov/air-trends/particulate-matter-pm10-trends
* https://www.arcgis.com/home/search.html?q=asthma
* https://www.cdc.gov/asthma/asthmadata.htm
* https://data.world/data-society/us-air-pollution-data
* https://public.tableau.com/app/profile/gell.rt.bodork.s/viz/Asthmacases/Sheet5?publish=yes
