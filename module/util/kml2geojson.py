# -*- coding: utf-8 -*-
import argparse

import os
import xml.etree.ElementTree as ET


class KMLParser(object):
    """
    This class is used to convert kml into geo json
    """
    def __init__(self):
        self.NS = {"gx": None}

    def setCollectionInst(self):
        self.features = []
        self.collection = {"type": "FeatureCollection", "features": self.features}

    def QName(self, name):
        # remove namespace-uri and return pure name
        if self.NS['gx'] is not None:
            return name.replace("{%s}" % self.NS['gx'], "")
        return name

    def PName(self, name):
        # return name with namespace-uri
        if self.NS['gx'] is not None:
            return "{%s}%s" % (self.NS['gx'], name)
        return name

    def __rangeContainer(self, element):
        """
        We set each Container (Document or Folder) as an item of
        feature collection, we didn't follow the tree structure
        that present in the original kml
        """
        features = self.features
        properties = {}
        style_dict = {}
        #
        # We have to parse Style first, then StyleMap, and then others
        #
        for child in element:
            _qtag = self.QName(child.tag)
            if _qtag == 'Style':
                self.__rangeStyle(child, style_dict)
        for child in element:
            _qtag = self.QName(child.tag)
            if _qtag == 'StyleMap':
                self.__rangeStyleMap(child, style_dict)

        for child in element:
            _qtag = self.QName(child.tag)
            if _qtag.lower() == 'name':
                properties['name'] = child.text.strip()
            elif _qtag == 'Document':
                self.__rangeContainer(child)
            elif _qtag == 'Folder':
                self.__rangeContainer(child)
            elif _qtag == 'Placemark':
                feature = self.__rangePlacemark(child)
                if feature is not None:
                    features.append(feature)
            elif _qtag == 'ExtendedData':
                self.__rangeExtendedData(child, properties)
            elif _qtag == 'description':
                self.__rangeDescription(child, properties)
            elif _qtag.lower() == 'geocode':
                properties.update({'geocode': child.text.strip()})

        if len(features) > 0:
            collection = self.collection
            if len(style_dict.keys()) > 0:
                if 'Style' in collection:
                    collection['style'].update(style_dict)
                else:
                    collection['style'] = style_dict
            if len(properties.keys()) > 0:
                if 'properties' in collection:
                    collection['properties'].update(properties)
                else:
                    collection['properties'] = properties

    def __rangeNode(self, node, props):
        _tag = self.QName(node.tag)
        props.update({_tag: ""})

        if _tag == "color":
            """
            sperate the color value into color and opacity
            exp: <color>22446688</color> -> color:#886644, opacity:0.2
            """
            if node.text:
                _color = node.text.strip()
                if len(_color) == 8:
                    props.update({"color": "#" + _color[6:8] + _color[4:6] + _color[2:4]})
                    _opacity = int(_color[0:2], 16) / 255.0
                    props.update({"opacity": "%f" % _opacity})

        elif node.text and len(node.text.strip()) > 0:
            props.update({_tag: node.text.strip()})
        elif len(list(node)) > 0:
            props.update({_tag: {}})
            for _fn in node:
                self.__rangeNode(_fn, props[_tag])

    def __rangeStyle(self, element, style_dict):
        _id = element.get('id', None)
        _style_rs = {}
        if _id:
            style_dict.update({_id: _style_rs})
            for child in element:
                self.__rangeNode(child, _style_rs)
        else:
            for child in element:
                self.__rangeNode(child, style_dict)

    def __rangeStyleMap(self, element, style_dict):
        id = element.get('id', None)
        if id is not None:
            _id = element.attrib['id']
            style_dict.update({_id: {}})

            pairs = element.findall(self.PName('Pair'))
            for pair in pairs:
                try:
                    _key = pair.find(self.PName('key')).text
                    if _key == "normal":
                        _url = pair.find(self.PName('styleUrl')).text[1:]
                        if _url in style_dict:
                            style_dict[_id] = style_dict[_url]
                except Exception as e:
                    pass

    def __rangePlacemark(self, element):
        feature = {}
        properties = {}
        style_dict = {}
        for child in element:
            _qtag = self.QName(child.tag)
            if _qtag.lower() == 'name':
                properties['name'] = child.text.strip()
            elif _qtag.lower() == 'geocode':
                properties.update({'geocode': child.text.strip()})
            elif _qtag == 'Style':
                self.__rangeStyle(child, style_dict)
            elif _qtag == 'styleUrl':
                properties['styleUrl'] = child.text.strip()
            elif _qtag == 'ExtendedData':
                self.__rangeExtendedData(child, properties)
            elif _qtag == 'description':
                self.__rangeDescription(child, properties)
            elif _qtag == 'MultiGeometry':
                geometries = self.__rangeMultiGeometry(child)
                feature = {"type": "GeometryCollection", "geometries": geometries}
            else:
                rs = self.__rangeGeometry(child)
                if rs is not None:
                    feature = {"type": "Feature", "geometry": rs}

        if len(feature.keys()) > 0:
            if len(style_dict.keys()) > 0:
                feature['Style'] = style_dict
            if len(properties.keys()) > 0:
                feature['properties'] = properties
            return feature
        return None

    def __rangeCoord(self, coord):
        pp = [float(p) for p in coord.text.split(',')[:2]]
        return pp

    def __rangeCoords(self, coords):
        pp = [[float(p) for p in pp.split(',')[:2]] for pp in coords.text.split()]
        return pp

    def __rangePoint(self, point):
        coordinates = point.find(self.PName('coordinates'))
        if coordinates is not None:
            pp = self.__rangeCoord(coordinates)
            return {"type": "Point", "coordinates": pp}
        return None

    def __rangePolygon(self, polygon):
        polys = []

        outerBoundaryIs = polygon.find(self.PName('outerBoundaryIs'))
        if outerBoundaryIs is not None:
            LinearRing = outerBoundaryIs.find(self.PName('LinearRing'))
            if LinearRing is not None:
                coordinates = LinearRing.find(self.PName('coordinates'))
                if coordinates is not None:
                    polys = [self.__rangeCoords(coordinates)]

        #
        #  Polygon with Inner Boundary
        #
        inners = polygon.findall(self.PName('innerBoundaryIs'))
        for innerBoundaryIs in inners:
            LinearRing = innerBoundaryIs.find(self.PName('LinearRing'))
            if LinearRing is not None:
                coordinates = LinearRing.find(self.PName('coordinates'))
                if coordinates is not None:
                    polys.append(self.__rangeCoords(coordinates))

        return {"type": "Polygon", "coordinates": polys}

    def __rangeLineString(self, line):
        try:
            _node = line.find(self.PName('coordinates'))

            if _node is not None:
                pp = self.__rangeCoords(_node)
            return {"type": "LineString", "coordinates": pp}

        except Exception as e:
            return None

    def __rangeGeometry(self, element):
        _qtag = self.QName(element.tag)
        if _qtag == 'Polygon':
            return self.__rangePolygon(element)
        if _qtag == 'LineString':
            return self.__rangeLineString(element)
        if _qtag == 'Point':
            return self.__rangePoint(element)
        return None

    def __rangeMultiGeometry(self, element):
        geometries = []
        for child in element:
            rs = self.__rangeGeometry(child)
            if rs is not None:
                geometries.append(rs)

        return geometries

    def __rangeDescription(self, element, props):
        if element.text and len(element.text) > 0:
            props.update({'description': element.text})

    def __rangeExtendedData(self, element, props):
        for child in element:
            _qtag = self.QName(child.tag)
            if _qtag == "SchemaData":
                self.__rangeSchemaData(child, props)
            elif _qtag == "Data":
                _node = child.find(self.PName('displayName'))
                if _node is not None and len(_node.text) > 0:
                    _displayName = _node.text
                else:
                    _displayName = None

                _key = child.get("name", None)
                if _key is None and _displayName is not None > 0:
                    _key = _node.text

                _value = child.find(self.PName('value'))
                if _key is not None and _value is not None:
                    props.update({_key: {'displayName': _displayName, 'value': _value.text}})

    def __rangeSchemaData(self, element, props):
        for child in element:
            _qtag = self.QName(child.tag)
            if _qtag == "SimpleData":
                _key = child.get("name", None)
                if _key and child.text:
                    props.update({_key: child.text})

    def convert_fromstring(self, str):
        root = ET.fromstring(str)
        _iter = root.getchildren()
        #
        # Get Namespace-uri
        #
        for element in _iter:
            if element.tag.startswith("{"):
                _end = element.tag.find('}')
                if _end > 1:
                    self.NS['gx'] = element.tag[1:_end]
            break

        self.setCollectionInst()
        self.__rangeContainer(_iter)

    def convert(self, file):
        collection_list = []
        for xcode in ['utf-8', 'big5']:
            try:
                ff = file.encode(xcode)
                if os.path.exists(ff):
                    _file = ff
                    break
            except:
                pass

        if os.path.exists(_file):
            if _file.endswith(b"kml"):
                f = open(_file, encoding='utf-8')
                kml_str = f.read()
                f.close()

                self.convert_fromstring(kml_str)
                collection_list.append(self.collection)

            elif _file.endswith(b"kmz"):

                import zipfile
                _kmz = zipfile.ZipFile(file)
                for _kml in _kmz.namelist():
                    if _kml.endswith(".kml"):
                        kml_str = _kmz.read(_kml)

                        self.convert_fromstring(str(kml_str, encoding="utf-8"))
                        collection_list.append(self.collection)
                _kmz.close()

            else:
                raise Exception('%s is not a kml file' % file)

        else:
            raise Exception('no such file %s' % file)

        return collection_list


def convert(src):
    """
    This is a shortcut caller that converting KML file and return GeoJson
    """
    parser = KMLParser()
    return parser.convert(src)


parser = argparse.ArgumentParser()
parser.add_argument('src', help='KML file path.')
parser.add_argument('output', nargs='?', help='KML file path.', default='.')


if __name__ == "__main__":
    args = parser.parse_args()
    src = args.src
    output = args.output

    rs = convert(src)

    class PrettyFloat(float):
        def __repr__(self):
            return '%.15g' % self

    def pretty_floats(obj):
        if isinstance(obj, float):
            return PrettyFloat(obj)
        elif isinstance(obj, dict):
            return dict((k, pretty_floats(v)) for k, v in obj.items())
        elif isinstance(obj, (list, tuple)):
            return map(pretty_floats, obj)
        return obj

    import json

    # 1.9999999999 -> 2 減少geojson的大小
    geojson = json.dumps(pretty_floats(rs), sort_keys=True, ensure_ascii=True, indent=4)

    with open(output, "w") as fout:
        fout.write(geojson)
