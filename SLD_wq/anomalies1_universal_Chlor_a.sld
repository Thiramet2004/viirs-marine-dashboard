<?xml version="1.0" encoding="UTF-8"?>
<sld:StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" version="1.0.0">
    <sld:UserLayer>
        <sld:LayerFeatureConstraints>
            <sld:FeatureTypeConstraint/>
        </sld:LayerFeatureConstraints>
        <sld:UserStyle>
            <sld:Name>chlor_a_anomalies</sld:Name>
            <sld:Title/>
            <sld:FeatureTypeStyle>
                <sld:Name>name</sld:Name>
                <sld:Rule>
                    <sld:RasterSymbolizer>
                        <sld:Geometry>
                            <ogc:PropertyName>grid</ogc:PropertyName>
                        </sld:Geometry>
                        <sld:ColorMap type="ramp">
                          <sld:ColorMapEntry color="#000064" opacity="1.0" label="-20 ug/L" quantity="-20.00"/>
                          <sld:ColorMapEntry color="#050582" opacity="1.0" label="-18 ug/L" quantity="-18.00"/>
                          <sld:ColorMapEntry color="#1414A5" opacity="1.0" label="-16 ug/L" quantity="-16.00"/>
                          <sld:ColorMapEntry color="#1E2AC3" opacity="1.0" label="-14 ug/L" quantity="-14.00"/>
                          <sld:ColorMapEntry color="#2146E1" opacity="1.0" label="-12 ug/L" quantity="-12.00"/>
                          <sld:ColorMapEntry color="#256EF9" opacity="1.0" label="-10 ug/L" quantity="-10.00"/>
                          <sld:ColorMapEntry color="#3099FF" opacity="1.0" label="-8 ug/L" quantity="-8.00"/>
                          <sld:ColorMapEntry color="#4BC8FF" opacity="1.0" label="-6 ug/L" quantity="-6.00"/>
                          <sld:ColorMapEntry color="#8CEBFF" opacity="1.0" label="-4 ug/L" quantity="-4.00"/>
                          <sld:ColorMapEntry color="#C8FAFF" opacity="1.0" label="-2 ug/L" quantity="-2.00"/>
                          <sld:ColorMapEntry color="#FFFFFF" opacity="1.0" label="0 ug/L" quantity="0.00"/>
                          <sld:ColorMapEntry color="#FFFAAA" opacity="1.0" label="2 ug/L" quantity="2.00"/>
                          <sld:ColorMapEntry color="#FFED50" opacity="1.0" label="4 ug/L" quantity="4.00"/>
                          <sld:ColorMapEntry color="#FFD21E" opacity="1.0" label="6 ug/L" quantity="6.00"/>
                          <sld:ColorMapEntry color="#FFA00A" opacity="1.0" label="8 ug/L" quantity="8.00"/>
                          <sld:ColorMapEntry color="#FA6904" opacity="1.0" label="10 ug/L" quantity="10.00"/>
                          <sld:ColorMapEntry color="#F03501" opacity="1.0" label="12 ug/L" quantity="12.00"/>
                          <sld:ColorMapEntry color="#D21000" opacity="1.0" label="14 ug/L" quantity="14.00"/>
                          <sld:ColorMapEntry color="#A50300" opacity="1.0" label="16 ug/L" quantity="16.00"/>
                          <sld:ColorMapEntry color="#870000" opacity="1.0" label="18 ug/L" quantity="18.00"/>
                          <sld:ColorMapEntry color="#6E0000" opacity="1.0" label="20 ug/L" quantity="20.00"/>
                        </sld:ColorMap>
                    </sld:RasterSymbolizer>
                </sld:Rule>
            </sld:FeatureTypeStyle>
        </sld:UserStyle>
    </sld:UserLayer>
</sld:StyledLayerDescriptor>
