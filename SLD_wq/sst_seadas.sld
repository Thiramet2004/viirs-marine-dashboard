<?xml version="1.0" encoding="UTF-8"?>
<sld:StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" version="1.0.0">
    <sld:UserLayer>
        <sld:LayerFeatureConstraints>
            <sld:FeatureTypeConstraint/>
        </sld:LayerFeatureConstraints>
        <sld:UserStyle>
            <sld:Name>MODIS_SST_20</sld:Name>
            <sld:Title/>
            <sld:FeatureTypeStyle>
                <sld:Name>SST_20</sld:Name>
                <sld:FeatureTypeName>Feature</sld:FeatureTypeName>
                <sld:Rule>
                    <sld:RasterSymbolizer>
                        <sld:Geometry>
                            <ogc:PropertyName>grid</ogc:PropertyName>
                        </sld:Geometry>
                        <sld:ColorMap type="ramp">
                            <sld:ColorMapEntry color="#0000FF" opacity="0.0" label="nodata" quantity="0"/>
                            <sld:ColorMapEntry color="#2307f1" opacity="1.0" label="0.2 Deg C" quantity="0.214"/>
                            <sld:ColorMapEntry color="#0a05b5" opacity="1.0" label="2.6 Deg C" quantity="2.606"/>
                            <sld:ColorMapEntry color="#094569" opacity="1.0" label="5.0 Deg C" quantity="5.003"/>
                            <sld:ColorMapEntry color="#076fa2" opacity="1.0" label="7.4 Deg C" quantity="7.400"/>
                            <sld:ColorMapEntry color="#0eaaa8" opacity="1.0" label="9.6 Deg C" quantity="9.614"/>
                            <sld:ColorMapEntry color="#10dce6" opacity="1.0" label="12.0 Deg C" quantity="12.006"/>
                            <sld:ColorMapEntry color="#12e1b3" opacity="1.0" label="14.4 Deg C" quantity="14.403"/>
                            <sld:ColorMapEntry color="#0fbd71" opacity="1.0" label="16.8 Deg C" quantity="16.800"/>
                            <sld:ColorMapEntry color="#0a8e4a" opacity="1.0" label="19.0 Deg C" quantity="19.014"/>
                            <sld:ColorMapEntry color="#2d9903" opacity="1.0" label="21.4 Deg C" quantity="21.406"/>
                            <sld:ColorMapEntry color="#74cb0b" opacity="1.0" label="23.8 Deg C" quantity="23.803"/>
                            <sld:ColorMapEntry color="#dee508" opacity="1.0" label="26.2 Deg C" quantity="26.200"/>
                            <sld:ColorMapEntry color="#dca705" opacity="1.0" label="28.4 Deg C" quantity="28.414"/>
                            <sld:ColorMapEntry color="#d94909" opacity="1.0" label="30.8 Deg C" quantity="30.806"/>
                            <sld:ColorMapEntry color="#b20a05" opacity="1.0" label="33.2 Deg C" quantity="33.203"/>
                            <sld:ColorMapEntry color="#6a1611" opacity="1.0" label="35.6 Deg C" quantity="35.600"/>
                            <sld:ColorMapEntry color="#81433e" opacity="1.0" label="37.8 Deg C" quantity="37.814"/>
                            <sld:ColorMapEntry color="#9f6e6d" opacity="1.0" label="40.2 Deg C" quantity="40.206"/>
                            <sld:ColorMapEntry color="#b79f9f" opacity="1.0" label="42.6 Deg C" quantity="42.603"/>
                            <sld:ColorMapEntry color="#000000" opacity="1.0" label="45.0 Deg C" quantity="45.000"/>
                        </sld:ColorMap>
                    </sld:RasterSymbolizer>
                </sld:Rule>
            </sld:FeatureTypeStyle>
        </sld:UserStyle>
    </sld:UserLayer>
</sld:StyledLayerDescriptor>
