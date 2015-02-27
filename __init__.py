# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VectorTextFieldStatistics
                                 A QGIS plugin
 VectorTextFieldStatistics
                             -------------------
        begin                : 2015-02-11
        copyright            : (C) 2015 by steven kay/geogeo
        email                : steven@geogeoglobal.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load VectorTextFieldStatistics class from file VectorTextFieldStatistics.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .VectorTextFieldStatistics import VectorTextFieldStatistics
    return VectorTextFieldStatistics(iface)
