<?

/*
Copyright(c)2008-2010 Internet Archive. Software license AGPL version 3.

This file is part of BookReader.

    BookReader is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    BookReader is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with BookReader.  If not, see <http://www.gnu.org/licenses/>.

    The BookReader source is hosted at http://github.com/openlibrary/bookreader/
*/

$item_id=$_GET['item_id'];
$path=$_GET['path'];
$doc=$_GET['doc'];
$callback=$_GET['callback'];
$human=$_GET['human'];

if (!$callback) {
    $callback = "";
}
if ($human) {
    $human = "--human";
}

function isValidCallback($identifier) {
    $pattern = '/^[a-zA-Z_$][a-zA-Z0-9_$]*$/';
    return preg_match($pattern, $identifier) == 1;
}

$contentType = 'application/json'; // default
if ($callback) {
    if (!isValidCallback($callback) ) {
        throw new Exception("Invalid callback");
    }
    $contentType = 'text/javascript'; // JSONP is not JSON
}

header('Content-type: ' . $contentType . ';charset=UTF-8');
header('Access-Control-Allow-Origin: *'); // allow cross-origin requests

$item_id = escapeshellarg($item_id);
$doc = escapeshellarg($doc);
$path = escapeshellarg($path);

# passthru("python analyze_ocr.py $human $item_id $doc $path $callback");
passthru("python analyze_ocr.py $human $item_id $doc $path $callback 2>&1");

#print('hello world');
#exec("python analyze_ocr.py $item_id $doc $path $callback 2>&1", $out, $retval);
#print $out;
#print $retval;
#printf('%s', implode('\n', $out));
?>
