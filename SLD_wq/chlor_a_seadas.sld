<?xml version="1.0" encoding="UTF-8"?>
<sld:StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" version="1.0.0">
    <sld:UserLayer>
        <sld:LayerFeatureConstraints>
            <sld:FeatureTypeConstraint/>
        </sld:LayerFeatureConstraints>
        <sld:UserStyle>
            <sld:Name>chlor_a</sld:Name>
            <sld:Title/>
            <sld:FeatureTypeStyle>
                <sld:Name>name</sld:Name>
                <sld:Rule>
                    <sld:RasterSymbolizer>
                        <sld:Geometry>
                            <ogc:PropertyName>grid</ogc:PropertyName>
                        </sld:Geometry>
                        <sld:ColorMap type="ramp">
                          <sld:ColorMapEntry color="#93006c" opacity="0.0" label="0.000 ug/L" quantity="0.000"/>
                          <sld:ColorMapEntry color="#93006c" opacity="1.0" label="0.010 ug/L" quantity="0.010"/>
                          <sld:ColorMapEntry color="#6f0090" opacity="1.0" label="0.014 ug/L" quantity="0.014"/>
                          <sld:ColorMapEntry color="#4800b7" opacity="1.0" label="0.021 ug/L" quantity="0.021"/>
                          <sld:ColorMapEntry color="#2100de" opacity="1.0" label="0.031 ug/L" quantity="0.031"/>
                          <sld:ColorMapEntry color="#000aff" opacity="1.0" label="0.046 ug/L" quantity="0.046"/>
                          <sld:ColorMapEntry color="#004aff" opacity="1.0" label="0.065 ug/L" quantity="0.065"/>
                          <sld:ColorMapEntry color="#0090ff" opacity="1.0" label="0.096 ug/L" quantity="0.096"/>
                          <sld:ColorMapEntry color="#00d5ff" opacity="1.0" label="0.142 ug/L" quantity="0.142"/>
                          <sld:ColorMapEntry color="#00ffd7" opacity="1.0" label="0.209 ug/L" quantity="0.209"/>
                          <sld:ColorMapEntry color="#00ff77" opacity="1.0" label="0.299 ug/L" quantity="0.299"/>
                          <sld:ColorMapEntry color="#00ff0f" opacity="1.0" label="0.440 ug/L" quantity="0.440"/>
                          <sld:ColorMapEntry color="#60ff00" opacity="1.0" label="0.649 ug/L" quantity="0.649"/>
                          <sld:ColorMapEntry color="#c8ff00" opacity="1.0" label="0.956 ug/L" quantity="0.956"/>
                          <sld:ColorMapEntry color="#ffeb00" opacity="1.0" label="1.368 ug/L" quantity="1.368"/>
                          <sld:ColorMapEntry color="#ffb700" opacity="1.0" label="2.014 ug/L" quantity="2.014"/>
                          <sld:ColorMapEntry color="#ff8300" opacity="1.0" label="2.968 ug/L" quantity="2.968"/>
                          <sld:ColorMapEntry color="#ff4f00" opacity="1.0" label="4.373 ug/L" quantity="4.373"/>
                          <sld:ColorMapEntry color="#ff1f00" opacity="1.0" label="6.256 ug/L" quantity="6.256"/>
                          <sld:ColorMapEntry color="#e60000" opacity="1.0" label="9.211 ug/L" quantity="9.211"/>
                          <sld:ColorMapEntry color="#a50000" opacity="1.0" label="13.573 ug/L" quantity="13.573"/>
                          <sld:ColorMapEntry color="#690000" opacity="1.0" label="20.000 ug/L" quantity="20.000"/>
                        </sld:ColorMap>
                    </sld:RasterSymbolizer>
                </sld:Rule>
            </sld:FeatureTypeStyle>
        </sld:UserStyle>
    </sld:UserLayer>
</sld:StyledLayerDescriptor>
